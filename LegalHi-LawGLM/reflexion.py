"""
Author: lihaitao
Date: 2024-07-26 12:46:27
LastEditors: Do not edit
LastEditTime: 2024-08-07 15:00:02
FilePath: /GLM2024/submit-image-demo/app/reflexion.py
"""

from LLM import *
from memory import *
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


def Reflexion(
    new_question,
    table_used_prompt,
    tool_prompt,
    answer,
    scratchpad,
    log_file,
    used_tools,
    needAPI,
    API_answer,
    API_answer_list,
    other_information,
):
    max_retries = 3
    flag = False
    question = new_question
    for attempt in range(max_retries):
        try:
            Memory_prompt = MEMORY_Refine_PROMPT.format(question=new_question, query_list=query_list)
            Memory_answer = LLM(Memory_prompt)
            Memory_response = prase_json_from_response(Memory_answer)
            Memory_list = Memory_response["相关问题"]
            memory = get_memory(Memory_list)
            break
        except:
            Memory_list = [1, 2, 3, 4]
            memory = get_memory(Memory_list)

    for attempt in range(max_retries):
        try:
            prompt = Self_Refine.format(
                question=new_question,
                table_used_prompt=table_used_prompt,
                tool_prompt=tool_prompt,
                wrong_scratchpad=scratchpad,
                answer=answer,
                example=memory,
                scratchpad=f"观察0: {answer}\n",
            )
            decompose_answer = LLM(prompt)
            decompose_response = prase_json_from_response(decompose_answer)
            break
        except:
            decompose_response = [{"思考": "分解行为错误，请思考表述重新尝试", "行动": "重新分解"}]
    # log_file.write('分解结果为:'+'\n' + str(decompose_response))

    try:
        thought = decompose_response[0]["思考"]
        action = decompose_response[0]["行动"]
    except Exception as e:
        thought = "思考错误"
        action = "行为错误"

    try:
        action_one = action.split("[")[0]
    except Exception as e:
        action_one = action[:3]

    Court_code = extract_court_code(action)
    if Court_code != None and flag == False:
        flag = True
        action += f"题目中有法院代字是{Court_code}，可以通过法院代字查询法院名称。"

    step = 1
    scratchpad = f"观察0: {answer}\n"
    Max_step = 9
    action_list = []
    other_observations = ""
    all_observations = f"观察0: {answer}\n"
    while True:
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

        if action_one == "查询":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新思考运行"
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

        if action_one == "查询统计":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新思考运行"

            answer = tongji_answer(action, ori_answer).replace("\n", " ")
            answer = refine_answer(action, answer).replace("\n", " ")

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

        if action_one == "查询筛选":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新思考运行"
            try:
                answer = filter_answer(action + other_information, ori_answer)

            except Exception as e:
                answer = ori_answer

            ### 统计
            ### 统计
            answer = "以下列出的都是满足筛选条件的信息" + str(answer)

            answer = tongji_answer(action + other_information, answer).replace("\n", " ")
            answer = refine_answer(action, answer).replace("\n", " ")

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

        if action_one == "查询排序":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误，重新思考运行"

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

            try:
                rank_result = Rank(action, ori_answer)
            except:
                rank_result = " "

            answer = refine_answer(action, ori_answer, rank_result).replace("\n", " ")
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

        if action_one == "查询求和":
            try:
                api_name, ori_answer, api_args, other_observation = Retrive(action, used_tools, log_file)
                other_observations += other_observation
            except Exception as e:
                ori_answer = "运行错误重新思考运行"

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

        if action_one == "结束":
            if needAPI:
                answer = final_api_answer(new_question, all_observations, API_answer)
            else:
                answer = final_answer(new_question, all_observations)
            return scratchpad, answer, other_observations

        if action_one == "重新分解":
            scratchpad += f"思考{step}: {thought}\n行动{step}: {action}\n观察{step}: 行动分解失败，没有按照正确分解格式，请仔细思考重新分解规划！\n"

        if step >= Max_step:
            if needAPI:
                answer = final_api_answer(new_question, all_observations, API_answer)
            else:
                answer = final_answer(new_question, all_observations)
            return scratchpad, answer, other_observations

        step += 1

        for attempt in range(3):
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

        action_one = action.split("[")[0]
