"""
Author: lihaitao
Date: 2024-07-22 23:13:43
LastEditors: Do not edit
LastEditTime: 2024-08-07 01:49:15
FilePath: /GLM2024/submit-image-demo/app/action.py
"""

from LLM import *
from produce_report import *
from utils import correct_args


def Retrive(action, used_tools, log_file):
    api_name, api_args = LLMs_tools(action, used_tools)

    api_name, api_args, other_observation = correct_args(api_name, api_args)

    ori_answer = http_api_call(api_name=api_name, data=api_args)

    if ori_answer["输出结果总长度"] == 0:
        if "案号" in api_args["query_conds"].keys():
            api_args["query_conds"]["案号"] = api_args["query_conds"]["案号"].replace("(", "（").replace(")", "）")
            ori_answer = http_api_call(api_name=api_name, data=api_args)

    return api_name, ori_answer, api_args, other_observation


def rank(keys: List, values: List[float], is_desc: bool = False):
    """
    rank keys by values
    """
    return [i[0] for i in sorted(zip(keys, values), key=lambda x: x[1], reverse=is_desc)]


def get_sum(nums: Union[List[float], List[str], List[int]]):
    if not isinstance(nums, list) or len(nums) == 0:
        return -100

    if any(not isinstance(x, (int, float, str)) for x in nums):
        return -100

    def map_str_to_num(str_num):
        try:
            str_num = str_num.replace("千", "*1e3")
            str_num = str_num.replace("万", "*1e4")
            str_num = str_num.replace("亿", "*1e8")
            return eval(str_num)
        except Exception as e:
            # logger.error(e)
            pass
        return -100

    if isinstance(nums[0], str):
        nums = [map_str_to_num(i) for i in nums]

    try:
        return sum(nums)
    except Exception as e:
        pass

    return -100


def Rank(action, ori_answer):
    output = ori_answer["输出结果"]
    list_number = []
    key = ""
    rank_prompt = RANK_KEY.format(action=action)
    rank_answer = LLM(rank_prompt)
    rank_response = prase_json_from_response(rank_answer)
    key = rank_response["Key"]
    keys = []

    for one_dict in output:
        try:
            keys.append(one_dict[key])
            one_dict[key] = one_dict[key].replace("千", "*1e3").replace("万", "*1e4").replace("亿", "*1e8")
            list_number.append(float(eval(one_dict[key])))
        except:
            continue

    rank_result = rank(keys, list_number, True)
    rank_number = 1
    rank_answer = f"{key}排序结果如下:\n"
    for one_result in rank_result:
        rank_answer += f"排序第{rank_number}的{key}为{one_result}\n"
        rank_number = rank_number + 1

    ensemble_prompt = RANK_ensemble.format(action=action, ori_answer=ori_answer["输出结果"], rank_result=rank_answer)

    ensemble_answer = LLM(ensemble_prompt)

    return ensemble_answer


def Sum(action, ori_answer):
    output = ori_answer["输出结果"]
    list_number = []
    key = ""
    rank_prompt = SUM_KEY.format(action=action)
    rank_answer = LLM(rank_prompt)
    rank_response = prase_json_from_response(rank_answer)
    key = rank_response["Key"]
    # keys = []

    if key == "涉案金额":
        for one_dict in output:
            try:
                list_number.append(float(one_dict[key]))
            except Exception as e:
                continue

    if key == "上市公司投资金额":
        for one_dict in output:
            try:
                # print("开始求和")
                if one_dict[key] != "":
                    list_number.append((one_dict[key]))
            except Exception as e:
                continue

    sum_result = get_sum(list_number)

    sum_answer = f"{key}求和结果如下:\n" + str(sum_result)

    ensemble_prompt = SUM_ensemble.format(action=action, ori_answer=ori_answer["输出结果"], rank_result=sum_answer)
    ensemble_answer = LLM(ensemble_prompt)
    return ensemble_answer


def filter_answer(question, answer):
    filter_output = []
    if isinstance(answer["输出结果"], list) and answer["输出结果总长度"] < 50:
        for a in answer["输出结果"]:
            try:
                new_a = a
                try:
                    if "案号" in a.keys():
                        new_a["起诉时间"] = a["案号"][1:5]
                    date_type = -1
                    if (
                        question.find("起诉时间") != -1
                        or question.find("起诉日期") != -1
                        or question.find("起诉") != -1
                    ):
                        date_type = 1
                    if (
                        question.find("立案时间") != -1
                        or question.find("立案日期") != -1
                        or question.find("立案") != -1
                    ):
                        date_type = 2
                    if (
                        question.find("审理时间") != -1
                        or question.find("审理日期") != -1
                        or question.find("审理") != -1
                    ):
                        date_type = 3
                    if date_type == 1 or date_type == 2:  # 对于起诉日期和立案日期，不需要日期字段
                        if "日期" in new_a.keys():
                            new_a.pop("日期")
                    if date_type == 3:  # 对于审理日期，不需要起诉时间字段
                        if "起诉时间" in new_a.keys():
                            new_a.pop("起诉时间")
                except:
                    pass
                prompt = ONE_Filter_prompt.format(question=str(question), answer=str(new_a))
                # print(prompt)
                a_answer = LLM(prompt)
                a_response = prase_json_from_response(a_answer)
                # print(a_response)
                if a_response["Filter_Answer"] == "True" or a_response["Filter_Answer"] == True:
                    filter_output.append(a)

            except Exception as e:
                # traceback.print_exc()
                filter_output.append(a)
    else:
        pass

    if len(filter_output) == 0:
        filter_output = answer["输出结果"]
    return {"输出结果总长度": len(filter_output), "输出结果": filter_output}
