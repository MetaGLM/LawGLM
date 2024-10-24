from zhipuai import ZhipuAI
import time
import json, re
from copy import deepcopy

from D_utils import multi_thread_excute
from D_LLM import LLM
from D_tools import TOOLS
from D_action import Action
from D_prompt import (
    API_MAP,
    EVALUATE_API_TASK,
    API_EXAMPLES,
    TEST_CHOOSE_TASK_PROMPT_SIMPLE_EXAMPLES,
    TEST_CHOOSE_TASK_PROMPT_WITHOUT_LIST_EXAMPLES,
    SUB_TASK_PROMPT_FILTER,
    SPECIFIC_API_CHOOSE_TASK_PROMPT,
)

from new_logtool import VLOG


def multi_get_solution(datalist, parallel_num=8):
    def get_solution(idata):
        xdata = deepcopy(idata)
        xdata["task_list"] = []
        xdata["is_sue"] = False

        if "起诉状" in xdata["question"]:
            new_task_list = Action.get_sue_task(question=xdata["question"])
            xdata["task_list"] = new_task_list
            xdata["is_sue"] = True
            xdata["API"] = []
            xdata["task_info"] = {"思考步骤": "", "API": []}
            return xdata

        api_choose_prompt = SPECIFIC_API_CHOOSE_TASK_PROMPT.format(question=xdata["question"])

        retry_times = 2
        for ii in range(retry_times):
            try:
                # * step1：生成解题思路
                try:
                    task_info = TOOLS.prase_json_from_response(
                        LLM.get_llm(api_choose_prompt, temperature=0.9, do_sample=True)
                    )
                except Exception as e:
                    VLOG[2](ii, "step1_json_fail:", e)
                    continue

                xdata["task_info"] = task_info

                solution = task_info["思考步骤"]
                api_list = task_info["API"]

                api_list_info = ""
                for api in set(api_list):
                    api_list_info = api + ":" + API_MAP.get(api, "") + "\n"
                xdata["API"] = api_list

                examples = ""

                for api in set(api_list):
                    examples += "\n\n".join(API_EXAMPLES.get(api, [])) + "\n\n"

                # * step3：生成解题步骤
                if "API4" in api_list or "API6" in api_list or "API7" in api_list:
                    prompt2 = TEST_CHOOSE_TASK_PROMPT_SIMPLE_EXAMPLES.format(
                        question=xdata["question"],
                        solution=solution,
                        api_list=api_list,
                        api_list_info=api_list_info,
                        examples=examples,
                    )
                else:
                    prompt2 = TEST_CHOOSE_TASK_PROMPT_WITHOUT_LIST_EXAMPLES.format(
                        question=xdata["question"],
                        solution=solution,
                        api_list=api_list,
                        api_list_info=api_list_info,
                        examples=examples,
                    )

                try:
                    task_list = TOOLS.prase_json_from_response(LLM.get_llm(prompt2, temperature=0.9, do_sample=True))
                except Exception as e:
                    VLOG[2](ii, "step3_json_fail:", e)
                    continue

                # * step4：优化解题步骤
                new_task_list = []
                for task in task_list:
                    if task["操作"] == "筛选":
                        prompt3 = SUB_TASK_PROMPT_FILTER.format(question=task["子任务"])
                        try:
                            sub_task_list = TOOLS.prase_json_from_response(LLM.get_llm(prompt3))
                            new_task_list.extend(sub_task_list)
                        except Exception as e:
                            VLOG[2](ii, "step4_json_fail:", e)
                            new_task_list.append(task)
                            continue
                    else:
                        new_task_list.append(task)
                        continue

                xdata["raw_task_list_{}".format(ii + 1)] = new_task_list

                # # 临时方案，放弃评估步骤，一次性生成解题步骤
                # xdata["task_list"] = new_task_list
                # return xdata

                new_api_list = []
                for task in new_task_list:
                    if "API" in task["操作"]:
                        if "列表" in task["操作"]:
                            new_api_list.append(task["操作"][2:])
                        else:
                            new_api_list.append(task["操作"])

                # * step5：评估解题步骤
                is_right_task = True

                if ii == retry_times - 1:
                    xdata["task_list"] = new_task_list
                    break

                # step5.1 评估操作是否合法
                for task in new_task_list:
                    if task["操作"] == "列表API查询":
                        is_right_task = False
                        break
                    if (
                        task["操作"] not in ("筛选", "排序", "索引", "计数", "求和", "分布统计", "提取", "总结")
                        and "API" not in task["操作"]
                    ):
                        is_right_task = False
                        VLOG[2]("WARNNING:", task)
                        break
                if not is_right_task:
                    VLOG[2]("step5.1_fail!")
                    continue

                # step5.2 评估第1个子任务是否符合要求
                if "API" not in new_task_list[0]["操作"]:
                    is_right_task = False
                    VLOG[2]("WARNNING:", new_task_list[0])
                if not is_right_task:
                    VLOG[2]("step5.2_fail!")
                    continue

                # step5.5 评估排序&索引步骤是否符合要求
                for i in range(len(new_task_list)):
                    task = new_task_list[i]
                    if task["操作"] == "排序":
                        if i == len(new_task_list) - 1 or new_task_list[i + 1]["操作"] != "索引":
                            is_right_task = False
                            VLOG[2]("WARNNING_SORT_INDEX_ERROR!")
                            break
                    if task["操作"] == "索引":
                        if i == 0 or new_task_list[i - 1]["操作"] != "排序":
                            is_right_task = False
                            VLOG[2]("WARNNING_SORT_INDEX_ERROR!")
                            break
                if not is_right_task:
                    VLOG[2]("step5.5_fail!")
                    continue

                # step5.6 评估API查询任务是否符合要求
                for task in new_task_list:
                    if "API" in task["操作"] and "列表" not in task["操作"]:
                        api_info = API_MAP.get(task["操作"], "")
                        prompt = EVALUATE_API_TASK.format(sub_task=task["子任务"], api_info=api_info)
                        res = LLM.get_llm(prompt)
                        VLOG[2]("SUB_TASK:", task["子任务"])
                        VLOG[2]("EVALUATE_API_TASK:", res)
                        if "yes" not in res:
                            is_right_task = False
                            VLOG[2]("WARNNING:", task)
                            break
                if not is_right_task:
                    VLOG[2]("step5.6_fail!")
                    continue

                if not is_right_task:
                    VLOG[2]("step5_final_fail!")
                    continue
                else:
                    xdata["task_list"] = new_task_list
                    break
            except Exception as e:
                VLOG[2](ii, "FINAL_ERROR:", e)
                continue

        return xdata

    all_results = multi_thread_excute([[get_solution, idata] for idata in datalist], parallel_num)

    results_solution = sorted(all_results, key=lambda x: x["id"])
    return results_solution


def multi_get_answer(datalist, parallel_num=8):
    def get_answer(idata):
        xdata = deepcopy(idata)
        xdata["answer"] = ""
        new_task_list = xdata.get("task_list", [])
        if len(new_task_list) == 0:
            VLOG[2]("NO_TASK_LIST!")
            return xdata

        check_api = False
        big_quetion = xdata["question"]
        solution = xdata["task_info"]["思考步骤"]
        if "API" in big_quetion or "接口" in big_quetion or "ＡＰＩ" in big_quetion or "api" in big_quetion:
            check_api = True

        retry_times = 1
        for ii in range(retry_times):
            is_right_answer = True
            try:
                context_data = {
                    "api_count": 0,
                    "api_type": [],
                    "history_data": [],
                    "is_sue": xdata["is_sue"],
                    "important": [],
                }
                if context_data["is_sue"]:
                    context_data["company_info1"] = []
                    context_data["company_info2"] = []
                    context_data["company_info3"] = []
                    context_data["company_info4"] = []
                    context_data["lawfirm_info1"] = []
                    context_data["lawfirm_info2"] = []

                task_index = 0
                previous_task = ""
                previous_answer = ""
                previous_data = []
                history_info = []
                api_data_list = []

                for task in new_task_list:
                    task_index += 1
                    context_data["current_task_index"] = task_index
                    new_task_question = ""
                    task_answer = ""

                    task_data = []
                    VLOG[2]("---" * 20)
                    VLOG[2](task_index, "STEP:", task)

                    sub_task = task["子任务"]

                    try:
                        if "API" in task["操作"] and "列表" not in task["操作"]:
                            new_task_question, task_answer, api_data_list, task_data, context_data = Action.retrieve(
                                task_index=task_index,
                                big_question=big_quetion,
                                sub_task=sub_task,
                                previous_task=previous_task,
                                previous_answer=previous_answer,
                                previous_data=previous_data,
                                history_info=history_info,
                                context_data=context_data,
                                solution=solution,
                                api=task["操作"],
                            )
                        elif "列表API" in task["操作"]:
                            api_key = task["操作"][2:]
                            task_answer, api_data_list = Action.multi_retrieve(
                                question=sub_task, api_key=api_key, api_data_list=api_data_list
                            )
                        elif task["操作"] == "计数":
                            task_answer = Action.stat_num(question=sub_task, api_data_list=api_data_list)
                        elif task["操作"] == "求和":
                            task_answer = Action.stat_sum(question=sub_task, api_data_list=api_data_list)
                        # elif task["操作"] == "提取法院代字":
                        #     task_answer = Action.caseid_parse(big_question=big_quetion, question=sub_task, previous_answer=previous_answer, api_data_list=api_data_list)
                        elif task["操作"] == "筛选":
                            task_answer, api_data_list = Action.filter_list(
                                question=sub_task, history_info=history_info, api_data_list=api_data_list
                            )
                        elif task["操作"] == "排序":
                            task_answer, api_data_list = Action.order(
                                question=sub_task, api_data_list=api_data_list, context_data=context_data
                            )
                        elif task["操作"] == "索引":
                            task_answer, api_data_list = Action.index(
                                question=sub_task,
                                history_info=history_info,
                                api_data_list=api_data_list,
                                context_data=context_data,
                            )
                        elif task["操作"] == "分布统计":
                            task_answer, api_data_list = Action.stat_analysis(
                                question=sub_task, history_info=history_info, api_data_list=api_data_list
                            )
                        elif task["操作"] in ("提取", "总结"):
                            task_answer = Action.summary(
                                question=sub_task, history_info=history_info, api_data_list=api_data_list
                            )
                        elif task["操作"] == "诉讼":
                            task_answer = Action.get_sue_info(question=big_quetion, context_data=context_data)
                            context_data["final_result"] = task_answer
                            break
                        else:
                            task_answer = Action.summary(
                                question=sub_task, history_info=history_info, api_data_list=api_data_list
                            )
                    except Exception as e:
                        VLOG[2]("!!!" * 20)
                        VLOG[2]("ERROR:", e)
                        VLOG[2]("!!!" * 10, task_index, task["操作"], sub_task)

                    previous_answer = task_answer
                    previous_task = sub_task
                    if task_data:
                        previous_data = task_data
                        for xtask_data in task_data:
                            if xtask_data not in context_data["history_data"]:
                                context_data["history_data"].append(xtask_data)
                    else:
                        previous_data = api_data_list
                        for xtask_data in api_data_list:
                            if xtask_data not in context_data["history_data"]:
                                context_data["history_data"].append(xtask_data)

                    intermediate_step = (
                        "中间步骤" + str(task_index) + ":\n子任务：" + sub_task + "\n子任务答案：" + task_answer
                    )
                    if check_api and task_index >= len(new_task_list):
                        intermediate_step += (
                            "\n实际调用API类型数：" + str(len(set(context_data["api_type"]))) + "类。\n"
                        )
                        if "次" in big_quetion or "ci" in big_quetion:
                            intermediate_step += (
                                "以上所有子任务步骤实际调用API次数：" + str(context_data["api_count"]) + "次；"
                            )
                        if "串" in big_quetion or "chuan" in big_quetion:
                            intermediate_step += "其中串行调用" + str(max(context_data["api_count"] - 1, 0)) + "次。\n"

                    history_info.append(intermediate_step)

                    VLOG[2](task_index, task["操作"], "\n", "TASK_ANSWER:", task_answer, "\nDATA:", api_data_list)

                # # 错误检查
                # if not is_right_answer:
                #     continue

                # VLOG[2]("***"*20)
                # VLOG[2]("FINAL_INFO:", history_info)
                # VLOG[2]("\n\n")
                # VLOG[2]("FINAL_CONTEXT_DATA:", context_data)
                # VLOG[2]("\n\n")
                # VLOG[2]("***"*20)
                # VLOG[2]("SOLUTION:", solution)
                # for i in range(len(new_task_list)):
                #     VLOG[2]("SUB_TASK"+str(i+1)+":", new_task_list[i])
                # VLOG[2]("#"*20)
                # VLOG[2](task_index, "FINAL_QUESTION:", xdata["question"])

                if context_data["is_sue"]:
                    final_answer = context_data.get("final_result", "")
                    xdata["answer"] = str(final_answer)
                    history_data = []
                else:
                    raw_final_answer = LLM.refine_answer_history(xdata["question"], history_info)
                    VLOG[2](task_index, "FINAL_ANSWER_RAW:", raw_final_answer)

                    history_data = list(set([str(x) for x in context_data["history_data"]]))
                    if (
                        "无法" in raw_final_answer
                        or "未" in raw_final_answer
                        or "建议" in raw_final_answer
                        or "注意" in raw_final_answer
                    ):
                        raw_final_answer = LLM.refine_answer_data(xdata["question"], history_info, history_data)
                        VLOG[2]("FINAL_ANSWER_REFINE_DATA:", raw_final_answer)

                    refine_final_answer = LLM.refine_answer_simple(
                        question=xdata["question"], answer=raw_final_answer, important=context_data["important"]
                    )
                    VLOG[2]("FINAL_ANSWER_REFINE_SIMPLE:", refine_final_answer)

                    final_answer = LLM.refine_answer_final(xdata["question"], refine_final_answer)
                    VLOG[2]("FINAL_ANSWER_REFINE:", final_answer)

                    xdata["answer"] = str(final_answer)
                    xdata["retry"] = str(ii + 1)
            except Exception as e:
                VLOG[2](ii, "FILNAL_ERROR:", e)
                continue
            if is_right_answer:
                break
        return xdata

    all_results = multi_thread_excute([[get_answer, idata] for idata in datalist], parallel_num)
    results_answer = sorted(all_results, key=lambda x: x["id"])
    return results_answer


if __name__ == "__main__":
    start = time.time()
    print("START_TIME:", start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    ### step1: 原始数据读取和处理
    # 本地测试
    question_file = "./question_c.json"
    # 线上提交
    # question_file = "/tcdata/question_c.json"
    original_datalist = [json.loads(x) for x in open(question_file, "r", encoding="utf-8").readlines() if x.strip()]

    for xdata in original_datalist:
        xdata["original_question"] = xdata["question"]
        xdata["question"] = LLM.refine_question(xdata["question"])
        xdata["answer"] = ""

    # datalist = [x for x in original_datalist if x["id"] % 20 == 5]
    datalist = sorted(
        original_datalist,
        key=lambda x: len(x["question"]) + 100 * x["question"].count("?") + 1000 * x["question"].count("起诉状"),
    )

    print("datalist_length:", len(datalist))
    print("TIME1:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    ### step2: 多线程获取解题思路和步骤
    results_solution = multi_get_solution(datalist, parallel_num=8)
    print("TIME2:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # # 文件保存
    # save_file2 = "./data/results_solution12.json"
    # with open(save_file2, "w", encoding="utf-8", errors="igonre") as f:
    #     for xdata in results_solution:
    #         f.write(json.dumps(xdata, ensure_ascii=False) + "\n")
    # print("FINISH_TIME3:", time.time()-start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    ### step4: 多线程获取答案
    # save_file2 = "./data/results_solution12.json"
    # datalist = [json.loads(x) for x in open(save_file2, "r", encoding="utf-8", errors="igonre").readlines() if x.strip()]
    datalist = results_solution

    results_answer = multi_get_answer(datalist, parallel_num=8)
    print("TIME4:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # # 文件保存
    # save_file4 = "./data/results_answer12.json"
    # with open(save_file4, "w", encoding="utf-8", errors="igonre") as f:
    #     for xdata in results_answer:
    #         f.write(json.dumps(xdata, ensure_ascii=False) + "\n")
    # print("FINISH_TIME4:", time.time()-start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # 最终文件保存
    results = results_answer
    # results_ids = [x["id"] for x in results_answer]
    # for xdata in original_datalist:
    #     if xdata["id"] not in results_ids:
    #         xdata["answer"] = ""
    #         results.append(xdata)
    results = sorted(results, key=lambda x: x["id"])

    final_bad_count = 0
    for xdata in results:
        if xdata["answer"] == "" or "无法" in xdata["answer"] or "未" in xdata["answer"]:
            final_bad_count += 1
    print("TIME5:", final_bad_count, time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    is_get_more = False
    ### 对回答无效的问题进行重新回答
    if 3600 - (time.time() - start) > 400:
        is_get_more = True
        for xdata in results:
            xdata["weight"] = 0
            if xdata["answer"] == "" or xdata["answer"] == xdata["question"]:
                xdata["weight"] = 100000 - len(xdata["question"])
            else:
                weight = 0
                if "无法" in xdata["answer"]:
                    weight += 10000
                elif "未" in xdata["answer"]:
                    weight += 1000
                weight -= 100 * xdata["question"].count("?")
                weight -= len(xdata["question"])
                xdata["weight"] = weight

        fix_num = 18
        if 3600 - (time.time() - start) > 1200:
            fix_num = 66
        elif 3600 - (time.time() - start) > 1100:
            fix_num = 60
        elif 3600 - (time.time() - start) > 1000:
            fix_num = 54
        elif 3600 - (time.time() - start) > 900:
            fix_num = 48
        elif 3600 - (time.time() - start) > 800:
            fix_num = 42
        elif 3600 - (time.time() - start) > 700:
            fix_num = 36
        elif 3600 - (time.time() - start) > 600:
            fix_num = 30
        elif 3600 - (time.time() - start) > 500:
            fix_num = 24

        datalist2 = sorted(deepcopy(results), key=lambda x: x["weight"], reverse=True)
        datalist2 = [x for x in datalist2 if x["weight"] > 0][0:fix_num]

        for xdata in datalist2:
            xdata["original_question"] = xdata["question"]
            xdata["question"] = LLM.refine_question(xdata["question"])
            xdata["answer"] = ""

        datalist2 = sorted(
            datalist2,
            key=lambda x: len(x["question"]) + 100 * x["question"].count("?") + 1000 * x["question"].count("起诉状"),
        )

        print("datalist2_length:", len(datalist2), fix_num)
        print("TIME6:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        ### step2: 多线程获取解题思路和步骤
        results_solution2 = multi_get_solution(datalist2, parallel_num=6)
        print("TIME7:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        datalist3 = results_solution2
        results_answer2 = multi_get_answer(datalist3, parallel_num=6)
        print("TIME8:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        new_results = results_answer2
        new_results_ids = [x["id"] for x in results_answer2]

        for xdata in results:
            if xdata["id"] not in new_results_ids:
                new_results.append(xdata)

        new_results = sorted(new_results, key=lambda x: x["id"])

        final_save_file = "result.json"
        with open(final_save_file, "w", encoding="utf-8", errors="igonre") as f:
            for xdata in new_results:
                xdata = {"id": xdata["id"], "question": xdata["original_question"], "answer": xdata["answer"]}
                f.write(json.dumps(xdata, ensure_ascii=False) + "\n")

        final_bad_count = 0
        for xdata in new_results:
            if xdata["answer"] == "" or "无法" in xdata["answer"] or "未" in xdata["answer"]:
                final_bad_count += 1

        print("TIME9:", final_bad_count, time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        results = new_results

    else:
        final_save_file = "result.json"

        final_bad_count = 0
        for xdata in results:
            if xdata["answer"] == "" or "无法" in xdata["answer"] or "未" in xdata["answer"]:
                final_bad_count += 1

        print("TIME9:", final_bad_count, time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        with open(final_save_file, "w", encoding="utf-8", errors="igonre") as f:
            for xdata in results:
                xdata = {"id": xdata["id"], "question": xdata["original_question"], "answer": xdata["answer"]}
                f.write(json.dumps(xdata, ensure_ascii=False) + "\n")
        print("TIME9_2:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    print("FINAL_TIME:", time.time() - start, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
