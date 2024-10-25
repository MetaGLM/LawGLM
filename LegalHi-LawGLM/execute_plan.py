"""
Author: lihaitao
Date: 2024-07-05 00:20:41
LastEditors: Do not edit
LastEditTime: 2024-08-07 14:59:48
FilePath: /GLM2024/submit-image-demo/app/execute_plan.py
"""

from LLM import *
from produce_report import *
from utils import *
from action import Retrive, Rank, Sum, filter_answer


def add_api_info_to_answer(question="", action="", answer="", api_name="", api_args=""):
    needFormerRes = ""
    try:
        for key in api_args["query_conds"]:
            value = api_args["query_conds"][key]
            if question.find(value) != -1:
                needFormerRes = "不依赖"
            else:
                needFormerRes = "依赖"
    except:
        needFormerRes = "不依赖"

    res = f"本步骤中调用了1次{api_name}，并且本次调用{needFormerRes}于前序结果\n"
    return res


def execute_plan(
    question,
    table_used_prompt,
    used_tools,
    memory,
    field_response,
    log_file,
    needAPI,
    API_answer,
    tool_prompt,
    API_answer_list,
    other_information,
):
    flag = False
    step = 0
    scratchpad = ""
    Max_step = 9
    API_answer = ""
    max_retries = 3
    action_list = []
    other_observations = ""
    all_observations = ""
    while True:
        step += 1

        if step == 1:
            Court_code = extract_court_code(question)
            if Court_code != None:
                question += f"题目中有法院代字{Court_code}，可以通过法院代字查询法院名称。"

        for attempt in range(max_retries):
            try:
                prompt = Action_Thought_prompt.format(
                    question=question,
                    table_used_prompt=table_used_prompt,
                    memory=memory,
                    field_response=field_response,
                    scratchpad=scratchpad,
                    tool_prompt=tool_prompt,
                )
                decompose_answer = LLM(prompt)
                decompose_response = prase_json_from_response(decompose_answer)
                break
            except Exception as e:
                decompose_response = [{"思考": "分解行为错误，请思考表述重新尝试", "行动": "重新分解"}]

        try:
            thought = decompose_response[0]["思考"]
            action = decompose_response[0]["行动"]
        except Exception as e:
            thought = "思考错误"
            action = "行为错误"
            # traceback.print_exc()

        if action not in action_list:
            action_list.append(action)
        else:
            try:
                action_prompt = Action_refine_prompt.format(
                    question=question,
                    table_used_prompt=table_used_prompt,
                    wrong_action=action,
                    scratchpad=scratchpad,
                    tool_prompt=tool_prompt,
                )
                Action_refine_answer = LLM(action_prompt)
                Action_decompose_response = prase_json_from_response(Action_refine_answer)
                thought = Action_decompose_response[0]["思考"]
                action = Action_decompose_response[0]["行动"]
                action_list.append(action)
            except:
                pass

        try:
            action_one = action.split("[")[0]
        except Exception as e:
            action_one = action[:3]

        if action.find("求和") != -1 or action.find("总额") != -1 or action.find("总金额") != -1:
            # print("修改为查询求和！")
            action_one = "查询求和"
        if (
            action.find("排序") != -1
            or action.find("最高") != -1
            or action.find("最低") != -1
            or action.find("第二高") != -1
        ):
            # print("修改为查询求和！")
            action_one = "查询排序"

        Court_code = extract_court_code(action)
        if Court_code != None and flag == False:
            flag = True
            thought += f"题目中有法院代字是{Court_code}，可以通过法院代字查询法院名称。"

        if action_one == "查询":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "查询失败，运行错误"

            answer = refine_answer(action, ori_answer).replace("\n", " ")  ###是否返回 检索长度

            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
                    if needAPI:
                        if ori_answer["输出结果"] not in API_answer_list:
                            API_answer_list.append(ori_answer["输出结果"])
                            try:
                                API_answer += add_api_info_to_answer(
                                    question=question,
                                    action=action,
                                    answer=API_answer,
                                    api_name=api_name,
                                    api_args=api_args,
                                )
                            except:
                                API_answer += "本步骤中调用了1次{api_name}"
            except:
                pass

            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: {answer}\n"

        elif action_one == "查询统计":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新运行"
            # 判断是否需要筛选
            # try:
            #     prompt = IF_Filter_prompt.format(action=action)
            #     if_filter_answer = LLM(prompt)
            #     if_filter_response = prase_json_from_response(if_filter_answer)
            # except:
            #     if_filter_response = {"Answer":False,"Filter_Content":"None"}

            # try:
            #     if if_filter_response['Answer'] == True or if_filter_response['Answer'] == "True":
            #         try:
            #             filter_action = action + if_filter_response['Filter_Content']
            #             ori_answer = filter_answer(filter_action,ori_answer)
            #         except Exception as e:
            #             ori_answer = ori_answer
            # except:
            #     pass
            ######
            answer = tongji_answer(action, ori_answer).replace("\n", " ")
            answer = refine_answer(action, ori_answer).replace("\n", " ")
            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
                    if needAPI:
                        if ori_answer["输出结果"] not in API_answer_list:
                            API_answer_list.append(ori_answer["输出结果"])
                            try:
                                API_answer += add_api_info_to_answer(
                                    question=question,
                                    action=action,
                                    answer=API_answer,
                                    api_name=api_name,
                                    api_args=api_args,
                                )
                            except:
                                API_answer += "本步骤中调用了1次{api_name}"
            except:
                pass
            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: {answer}\n"

        elif action_one == "查询筛选":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新运行"
            try:
                answer = filter_answer(action + other_information, ori_answer)
            except Exception as e:
                answer = ori_answer

            ### 判断下一步需要干什么操作。
            ### 统计
            answer = "以下列出的都是满足筛选条件的信息" + str(answer)

            answer = tongji_answer(action + other_information, answer).replace("\n", " ")
            answer = refine_answer(action, answer).replace("\n", " ")

            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
            except:
                pass

            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
                    if needAPI:
                        if ori_answer["输出结果"] not in API_answer_list:
                            API_answer_list.append(ori_answer["输出结果"])
                            try:
                                API_answer += add_api_info_to_answer(
                                    question=question,
                                    action=action,
                                    answer=API_answer,
                                    api_name=api_name,
                                    api_args=api_args,
                                )
                            except:
                                API_answer += "本步骤中调用了1次{api_name}"
            except:
                pass

            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: {answer}\n"

        elif action_one == "查询排序":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行失败，重新运行"

            ### 判断是否需要筛选
            try:
                prompt = IF_Filter_prompt.format(action=action)
                if_filter_answer = LLM(prompt)
                if_filter_response = prase_json_from_response(if_filter_answer)
            except:
                if_filter_response = {"Answer": False, "Filter_Content": "None"}

            try:
                if if_filter_response["Answer"] == True or if_filter_response["Answer"] == "True":
                    try:
                        filter_action = action + if_filter_response["Filter_Content"]
                        ori_answer = filter_answer(filter_action, ori_answer)
                    except Exception as e:
                        ori_answer = ori_answer
            except:
                pass
            ######
            try:
                rank_result = Rank(action, ori_answer)
            except:
                rank_result = ""
            # print(rank_result)
            answer = refine_answer(action, rank_result, rank_result).replace("\n", " ")
            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
                    if needAPI:
                        if ori_answer["输出结果"] not in API_answer_list:
                            API_answer_list.append(ori_answer["输出结果"])
                            try:
                                API_answer += add_api_info_to_answer(
                                    question=question,
                                    action=action,
                                    answer=API_answer,
                                    api_name=api_name,
                                    api_args=api_args,
                                )
                            except:
                                API_answer += "本步骤中调用了1次{api_name}"
            except:
                pass

            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: {answer}\n"

        elif action_one == "查询求和":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误"

            try:
                prompt = IF_Filter_prompt.format(action=action)
                if_filter_answer = LLM(prompt)
                if_filter_response = prase_json_from_response(if_filter_answer)

            except:
                if_filter_response = {"Answer": "False", "Filter_Content": "None"}
            try:
                if if_filter_response["Answer"] == True or if_filter_response["Answer"] == "True":
                    try:
                        filter_action = action + if_filter_response["Filter_Content"]
                        ori_answer = filter_answer(filter_action, ori_answer)
                    except:
                        ori_answer = ori_answer
            except:
                pass
            ######

            try:
                sum_result = Sum(action, ori_answer)
            except:
                sum_result = ""
            answer = refine_answer(action, ori_answer, sum_result).replace("\n", " ")

            try:
                if ori_answer["输出结果总长度"] != 0 and type(ori_answer["输出结果"]) != str:
                    all_observations += f"行动{step}: {action} 观察{step}: {answer}\n"
                    if needAPI:
                        if ori_answer["输出结果"] not in API_answer_list:
                            API_answer_list.append(ori_answer["输出结果"])
                            try:
                                API_answer += add_api_info_to_answer(
                                    question=question,
                                    action=action,
                                    answer=API_answer,
                                    api_name=api_name,
                                    api_args=api_args,
                                )
                            except:
                                API_answer += "本步骤中调用了1次{api_name}"
            except:
                pass

            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: {answer}\n"

        elif action_one == "重新分解":
            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: 行动分解失败，没有按照正确分解格式，请仔细思考重新分解规划！\n"
        elif action_one == "结束":
            if needAPI:
                answer = final_api_answer(question, all_observations, API_answer)
            else:
                answer = final_answer(question, all_observations)
            return scratchpad, answer, API_answer, other_observations
        else:
            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: 行动分解错误，没有按照正确分解格式或行动不在六种规定的行动范围内！\n"

        if step >= Max_step:
            if needAPI:
                answer = final_api_answer(question, all_observations, API_answer)
            else:
                answer = final_answer(question, all_observations)
            return scratchpad, answer, API_answer, other_observations
