import json, re
import concurrent.futures
from tqdm import tqdm


from typing import Iterable
import jsonlines
from apis.api import *
from config import *
from model import call_glm
from prompts import pre_check_company_name_prompt


# 定义一个函数read_jsonl，用于读取jsonl文件
def read_jsonl(path):
    # 初始化一个空列表，用于存储读取到的内容
    content = []
    # 使用jsonlines库打开jsonl文件，并设置为只读模式
    with jsonlines.open(path, "r") as json_file:
        # 遍历json文件的每一行，将其转换为字典类型
        for obj in json_file.iter(type=dict, skip_invalid=True):
            # 将每一行添加到content列表中
            content.append(obj)
    # 返回content列表
    return content


def save_answers(
    queries: Iterable,
    results: Iterable,
    result_file: str = "./data/results/伍柒_result.json",
):
    answers = []
    for query, result in zip(queries, results):
        answers.append({"id": query["id"], "question": query["question"], "answer": result})

    # use jsonlines to save the answers
    def write_jsonl(path, content):
        with jsonlines.open(path, "w") as json_file:
            json_file.write_all(content)

    # 保存答案 result_file 指定位置
    write_jsonl(result_file, answers)


def read_txt_file_to_list(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # 使用列表推导式将每一行转换为列表的元素
            data_list = [line.strip() for line in file]
            data_list = [ele for ele in data_list if ele != ""]
        return data_list
    except FileNotFoundError as e:
        print_log(f"File {file_path} not found.")
        raise e


def convert_to_float(s):
    if s is None:
        return 0

    # 使用正则表达式将字符串中的数字和中文符号替换为英文符号
    s = s.replace("亿", "e8").replace("万", "e4")

    try:
        # 使用float函数将字符串转换为浮点数
        result = float(s)
    except Exception as e:
        result = 0

    return result


def convert_to_str(f):
    if f > 1e8:
        f = f / 1e8
        return f"{round(f, 2):.2f}" + "亿"
    if f > 1e4:
        f = f / 1e4
        return f"{round(f, 2):.2f}" + "万"
    return f"{round(f, 2):.2f}"


def convert_date_2_answer_format(date):
    try:
        year_str = date.split("年")[0]
        last_str = date.split("年")[-1]
        month_str = last_str.split("月")[0]
        month_str = "0" + month_str if len(month_str) == 1 else month_str
        day_str = last_str.split("月")[-1].replace("日", "")
        day_str = "0" + day_str if len(day_str) == 1 else day_str
        return year_str + "年" + month_str + "月" + day_str + "日"
    except Exception as e:
        print_log(str(e))
        return date


def multi_thread_excute(all_tasks, parralle_num=20):
    """
    多线程运行任务，注意，返回结果序并不和all_tasks一致，请设计好task的输出，能够通过map的形式找到对应的答案
    """

    def multi_thread_excute_helper(tasks):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            exe_tasks = [executor.submit(*task) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(exe_tasks)]
        return results

    all_results = []
    for i in tqdm(range(0, len(all_tasks), parralle_num)):
        all_results += multi_thread_excute_helper(all_tasks[i : i + parralle_num])
    return all_results


def parse_json_from_response(rsp: str):
    pattern = r"```json(.*?)```"
    rsp_json = None
    try:
        match = re.search(pattern, rsp, re.DOTALL)
        if match is not None:
            try:
                rsp_json = json.loads(match.group(1).strip())
            except:
                pass
        else:
            rsp_json = json.loads(rsp)
        return rsp_json
    except json.JSONDecodeError as e:
        raise ("Json Decode Error: {error}".format(error=e))


def parse_content_2_function_call(content, response):
    message = response.choices[0].message.model_dump()
    try:
        if content.__contains__("```python"):
            # function = parse_method_call(content)
            function = parse_method_call_v2(content)

            message = {
                "content": "",
                "role": "assistant",
                "tool_calls": [
                    {"id": "call_8807505746892927304", "function": function, "type": "function", "index": 0}
                ],
            }

            response.choices[0].finish_reason = "tool_calls"
            return message, response
    except Exception as e:
        print_log(str(e))

    method_name = check_method_name_in_llm_response(content)
    if method_name:
        try:
            method_index = content.find(method_name) + len(method_name)
            content_after_method = content[method_index:]
            right_index = 0
            if content_after_method.__contains__("(") and content_after_method.__contains__(")"):
                left_index = content_after_method.find("(")
                right_index = content_after_method.rfind(")")
            elif content_after_method.__contains__("{") and content_after_method.__contains__("}"):
                left_index = content_after_method.find("{")
                right_index = content_after_method.rfind("}")
            if right_index > 0:
                params_content = content_after_method[left_index + 1 : right_index].strip()
                params_content = params_content.replace("'", "").replace('"', "")
                if params_content.__contains__(","):
                    params_list = params_content.split(",")
                else:
                    params_list = [params_content]
                params_dict = {}
                for param in params_list:
                    key = None
                    if param.__contains__("="):
                        key, value = param.split("=")
                    elif param.__contains__(":"):
                        key, value = param.split(":")
                    if key:
                        key = key.strip()
                        value = value.strip()
                        params_dict[key] = value
                if params_dict:
                    function = {
                        "name": method_name,
                        "arguments": json.dumps(params_dict, ensure_ascii=False),  # 返回解析后的参数字典
                    }

                    message = {
                        "content": "",
                        "role": "assistant",
                        "tool_calls": [
                            {"id": "call_8807505746892927304", "function": function, "type": "function", "index": 0}
                        ],
                    }

                    response.choices[0].finish_reason = "tool_calls"
                    return message, response

        except Exception as e:
            return message, response

    return message, response


def check_method_name_in_llm_response(content):
    method_names = [
        "get_address_code",
        "get_address_info",
        "get_company_info",
        "get_company_register",
        "get_company_register_name",
        "get_court_code",
        "get_court_info",
        "get_lawfirm_info",
        "get_lawfirm_log",
        "get_legal_abstract",
        "get_legal_document",
        "get_legal_document_list",
        "get_sub_company_info",
        "get_sub_company_info_list",
        "get_temp_info",
        "get_xzgxf_info",
        "get_xzgxf_info_list",
    ]
    for method_name in method_names:
        if method_name in content:
            return method_name
    return False


def parse_method_call(method_call_str):
    # 正则表达式匹配方法名和参数
    method_pattern = r"(\w+)\n```python\ntool_call\((.*?)\)\n```"
    match = re.search(method_pattern, method_call_str, re.DOTALL)

    if match:
        method_name = match.group(1)
        params_str = match.group(2)

        # 处理参数字符串
        # 将参数字符串中的等号替换为冒号
        params_str = params_str.replace("=", ":")
        # 匹配字符串参数并确保键周围有双引号
        params_str = re.sub(r"(\w+)(\s*:\s*)([^,]+)", r'"\1"\2\3', params_str)
        # 处理数组字符串，移除数组字符串外的单引号
        params_str = re.sub(r"'(\[.*?\])'", r"\1", params_str)
        # 将单引号替换为双引号，以便json解析
        params_str = params_str.replace("'", '"')
        params_str = "{" + params_str + "}"
        # 将参数字符串转换为字典
        params_dict = json.loads(params_str)

        return {"name": method_name, "arguments": params_str}
    else:
        raise ValueError("Method call string does not match the expected format.")


def parse_method_call_v2(method_call_str):
    # 修改后的正则表达式匹配方法名和参数，考虑了周围可能存在的空格
    # method_pattern = r'\s*(\w+)\s*\n\s*```\s*python\s*\n\s*tool_call\s*\((.*?)\)\s*\n\s*```\s*'
    method_pattern = r"\s*(\w+)\s*\n\s*```\s*python\s*\n\s*tool_call\s*\((.*?)\)\s*"
    match = re.search(method_pattern, method_call_str, re.DOTALL)

    if match:
        method_name = match.group(1).strip()  # 去除可能的前后空格
        params_str = match.group(2)

        # 处理参数字符串
        # 将参数字符串中的等号替换为冒号
        params_str = params_str.replace("=", ":")
        # 匹配字符串参数并确保键周围有双引号
        params_str = re.sub(r"(\w+)(\s*:\s*)([^,]+)", r'"\1"\2\3', params_str)
        # 处理数组字符串，移除数组字符串外的单引号
        params_str = re.sub(r"'(\[.*?\])'", r"\1", params_str)
        # 将单引号替换为双引号，以便json解析
        params_str = params_str.replace("'", '"')
        params_str = "{" + params_str + "}"
        # 将参数字符串转换为字典
        params_dict = json.loads(params_str)

        # 返回结果中的arguments应该是params_dict而不是params_str，因为params_str是JSON字符串
        return {
            "name": method_name,
            "arguments": params_str,  # 返回解析后的参数字典
        }
    else:
        raise ValueError("Method call string does not match the expected format.")


def check_company_name(tool_name, args, logic_chain, must_contained_info):
    try:
        args_json = json.loads(args)
        company_short_name, company_full_name = "", ""
        if "key" in args_json.keys() and args_json["key"] == "公司名称" and "value" in args_json.keys():
            company_short_name = args_json["value"]
        elif "company_name" in args_json.keys():
            company_short_name = args_json["company_name"]
        elif "sub_company_name" in args_json.keys():
            company_short_name = args_json["sub_company_name"]
        elif "related_parent_company_name" in args_json.keys():
            company_short_name = args_json["related_parent_company_name"]
        if company_short_name:
            tried_result = try_find_correct_name(company_short_name, args_json, logic_chain, must_contained_info)
            if tried_result:
                return tried_result
            else:
                messages = [
                    {"role": "system", "content": pre_check_company_name_prompt},
                    {"role": "user", "content": company_short_name},
                ]
                response = call_glm(messages, model="glm-4-0520", temperature=0.11, top_p=0.11)
                company_info = parse_json_from_response(response.choices[0].message.content)
                if company_info.get("fixed_info"):
                    tried_result = try_find_correct_name(
                        company_info.get("fixed_info"), args_json, logic_chain, must_contained_info
                    )
                    if tried_result:
                        return tried_result

        if tool_name == "get_company_info":
            company_short_name, company_full_name = "", ""
            if "公司名称" in args_json.keys():
                company_short_name = args_json.get("value", "")
                params = {"query_conds": {"公司简称": company_short_name}, "need_fields": ["公司名称"]}
                api_result = http_api_call("get_company_info", params)
                api_return_result = api_result.get("return", [])
                if len(api_return_result) == 1 and api_return_result[0].get("公司名称", ""):
                    company_full_name = api_return_result[0].get("公司名称", "")
                    args_json["公司名称"] = company_full_name
            elif "公司简称" in args_json.keys():
                company_full_name = args_json.get("value", "")
                params = {"query_conds": {"公司名称": company_full_name}, "need_fields": ["公司简称"]}
                api_result = http_api_call("get_company_info", params)
                api_return_result = api_result.get("return", [])
                if len(api_return_result) == 1 and api_return_result[0].get("公司简称", ""):
                    company_short_name = api_return_result[0].get("公司简称", "")
                    args_json["公司简称"] = company_short_name
            return json.dumps(args_json, ensure_ascii=False)
    except Exception as e:
        print_log(str(e))
        return args
    return args
    pass


def try_find_correct_name(company_short_name, args_json, logic_chain, must_contained_info):
    params = {"query_conds": {"公司简称": company_short_name}, "need_fields": ["公司名称"]}
    api_result = http_api_call("get_company_info", params)
    api_return_result = api_result.get("return", [])
    if len(api_return_result) == 1 and api_return_result[0].get("公司名称", ""):
        company_full_name = api_return_result[0].get("公司名称", "")
        if "key" in args_json.keys() and args_json["key"] == "公司名称" and "value" in args_json.keys():
            args_json["value"] = company_full_name
        elif "company_name" in args_json.keys():
            args_json["company_name"] = company_full_name
        elif "sub_company_name" in args_json.keys():
            args_json["sub_company_name"] = company_full_name
        elif "related_parent_company_name" in args_json.keys():
            args_json["related_parent_company_name"] = company_full_name

        # logic_chain.append('{}的公司全称是:{}'.format(company_short_name, company_full_name))
        logic_chain.append(["简称" + company_short_name, "get_company_info", "公司的全称是" + company_full_name])
        must_contained_info.add(company_short_name)
        must_contained_info.add(company_full_name)
        return json.dumps(args_json, ensure_ascii=False)

    params = {"query_conds": {"公司代码": company_short_name}, "need_fields": ["公司名称"]}
    api_result = http_api_call("get_company_info", params)
    api_return_result = api_result.get("return", [])
    if len(api_return_result) == 1 and api_return_result[0].get("公司名称", ""):
        company_full_name = api_return_result[0].get("公司名称", "")
        if "key" in args_json.keys() and args_json["key"] == "公司名称" and "value" in args_json.keys():
            args_json["value"] = company_full_name
        elif "company_name" in args_json.keys():
            args_json["company_name"] = company_full_name
        elif "sub_company_name" in args_json.keys():
            args_json["sub_company_name"] = company_full_name
        elif "related_parent_company_name" in args_json.keys():
            args_json["related_parent_company_name"] = company_full_name

        logic_chain.append(["公司代码" + company_short_name, "get_company_info", "公司名称是" + company_full_name])
        must_contained_info.add(company_short_name)
        must_contained_info.add(company_full_name)
        return json.dumps(args_json, ensure_ascii=False)

    params = {"query_conds": {"统一社会信用代码": company_short_name}, "need_fields": []}
    api_result = http_api_call("get_company_register_name", params)
    # api_return_result = api_result.get('return', [])
    if (
        type(api_result) == dict
        and "return" in api_result.keys()
        and len(api_result["return"]) > 0
        and api_result["return"][0].get("公司名称", "")
    ):
        company_full_name = api_result["return"][0].get("公司名称", "")
        if "key" in args_json.keys() and args_json["key"] == "公司名称" and "value" in args_json.keys():
            args_json["value"] = company_full_name
        elif "company_name" in args_json.keys():
            args_json["company_name"] = company_full_name
        elif "sub_company_name" in args_json.keys():
            args_json["sub_company_name"] = company_full_name
        elif "related_parent_company_name" in args_json.keys():
            args_json["related_parent_company_name"] = company_full_name

        logic_chain.append(
            ["统一社会信用代码" + company_short_name, "get_company_register_name", "公司名称是" + company_full_name]
        )
        must_contained_info.add(company_short_name)
        must_contained_info.add(company_full_name)
        return json.dumps(args_json, ensure_ascii=False)

    params = {"query_conds": {"公司名称": company_short_name}, "need_fields": []}
    api_result_1 = http_api_call_original("get_company_info", params)
    api_result_2 = http_api_call_original("get_company_register", params)
    if len(api_result_1) > 0 or len(api_result_2) > 0:
        if "key" in args_json.keys() and args_json["key"] == "公司名称" and "value" in args_json.keys():
            args_json["value"] = company_short_name
        elif "company_name" in args_json.keys():
            args_json["company_name"] = company_short_name
        elif "sub_company_name" in args_json.keys():
            args_json["sub_company_name"] = company_short_name
        elif "related_parent_company_name" in args_json.keys():
            args_json["related_parent_company_name"] = company_short_name
        return json.dumps(args_json, ensure_ascii=False)

    return None


def check_area_4_temperature(tool_name, args, logic_chain, message):
    try:
        if tool_name in ["get_temp_info", "get_address_code"]:
            args_json = json.loads(args)
            if len(logic_chain) and len(logic_chain[-1]) == 3 and type(logic_chain[-1][-1]) == dict:
                address = ""
                last_dict = logic_chain[-1][-1]
                for key, value in last_dict.items():
                    if key.__contains__("地址"):
                        address = value
                        break
                if address:
                    message["tool_calls"][0]["function"]["name"] = "get_address_info"
                    tool_name = "get_address_info"

                    params = {"address": address}
                    params = json.dumps(params, ensure_ascii=False)
                    message["tool_calls"][0]["function"]["arguments"] = params
                    args = params
    except Exception as e:
        print_log(str(e))
        return args, tool_name
    return args, tool_name
    pass


def check_target_property(table_properties, target_properties):
    for target_property in target_properties:
        if not target_property in table_properties:
            return False
    return True


def update_logic_chain_and_messages(new_condition, logic_chain, messages):
    if len(logic_chain) >= 2 and type(logic_chain[-2]) == list:
        if len(logic_chain[-2]) == 3 and type(logic_chain[-2][-1]) == dict and len(logic_chain[-2][-1]) > 5:
            old_search_result = logic_chain[-2][-1]
            for key, value in old_search_result.items():
                if value == new_condition:
                    logic_chain[-2][-1] = {key, value}

                    if (
                        len(messages) >= 2
                        and messages[-2].get("role", "") == "tool"
                        and messages[-2].get("content", "").__contains__(":")
                    ):
                        messages[-2]["content"] = (
                            messages[-2]["content"].split(":")[0] + ":" + str(logic_chain[-2][-1])
                        )
                    break


def format_date(match):
    year = match.group(1)
    month = match.group(2).zfill(2)  # 如果不足两位，前面补0
    day = match.group(3).zfill(2)  # 如果不足两位，前面补0
    return f"{year}年{month}月{day}日"


def final_post_process(answer):
    # 定义正则表达式
    date_pattern = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
    # 使用正则表达式的sub方法和替换函数
    formatted_text = date_pattern.sub(format_date, answer)

    result = formatted_text.replace("（", "(").replace("）", ")")
    return result


if __name__ == "__main__":
    # content = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市', court_name='鄯善县人民法院') \n```"
    # content = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市')"
    # function = parse_method_call_v2(content)
    # #
    # # # content = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市', court_name='鄯善县人民法院')\n```"
    # # # function = parse_method_call(content)
    #
    #
    # method_call_str = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市', court_name='鄯善县人民法院') \n```"
    # # method_call_str = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市', court_name='鄯善县人民法院')\n```"
    # method_call_str = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市')"
    #
    # method_pattern = r'(\w+)\n```python\ntool_call\((.*?)\)\n```'
    # method_pattern = r'\s*(\w+)\s*\n\s*```\s*python\s*\n\s*tool_call\s*\((.*?)\)\s*'
    #
    # match = re.search(method_pattern, method_call_str, re.DOTALL)
    # if match:
    #     print(match.group(1))
    # else:
    #     print("No match found.")

    # # content = "get_temp_info\n```python\ntool_call(date='2020年11月6日', province='新疆维吾尔自治区', city='吐鲁番市', court_name='鄯善县人民法院') \n```"
    # content = "get_legal_document\n```python\ntool_call(case_num=\"(2020)皖1202民初1067号\")\n```"
    # # content = 'get_address_info\n{"address": "浙江省杭州市滨江区丹枫路799号"}'
    # method_name = check_method_name_in_llm_response(content)
    # method_index = content.find(method_name) + len(method_name)
    # content_after_method = content[method_index:]
    # right_index = 0
    # if content_after_method.__contains__("(") and content_after_method.__contains__(")"):
    #     left_index = content_after_method.find("(")
    #     right_index = content_after_method.rfind(")")
    # elif content_after_method.__contains__("{") and content_after_method.__contains__("}"):
    #     left_index = content_after_method.find("{")
    #     right_index = content_after_method.rfind("}")
    # if right_index > 0:
    #     params_content = content_after_method[left_index + 1:right_index].strip()
    #     params_content = params_content.replace("'", "").replace('"', "")
    #     if params_content.__contains__(","):
    #         params_list = params_content.split(",")
    #     else:
    #         params_list = [params_content]
    #     params_dict = {}
    #     for param in params_list:
    #         key = None
    #         if param.__contains__("="):
    #             key, value = param.split("=")
    #         elif param.__contains__(":"):
    #             key, value = param.split(":")
    #         if key:
    #             key = key.strip()
    #             value = value.strip()
    #             params_dict[key] = value
    #     if params_dict:
    #         function = {
    #             'name': method_name,
    #             'arguments': json.dumps(params_dict, ensure_ascii=False)  # 返回解析后的参数字典
    #         }
    #
    #         message = {"content": "",
    #                    "role": "assistant",
    #                    "tool_calls": [
    #                        {
    #                            "id": "call_8807505746892927304",
    #                            "function": function,
    #                            "type": "function",
    #                            "index": 0
    #
    #                        }
    #                    ]
    #                    }
    #
    #     pass
    pass
