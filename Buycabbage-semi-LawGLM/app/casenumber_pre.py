# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 09:25:41 2024

@author: 86187
"""

import json
import requests
from zhipuai import ZhipuAI
import re

client = ZhipuAI()
need_fields = []
domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 3BC078EB97F78FB2ABC6B2825A1FE57F783DF2BEE85336CC",  # 团队token:D49……
}


# 5
def get_legal_document(case_number: str, need_fields: list = None) -> dict:
    """
    根据案号查询裁判文书相关信息。
    参数:
    - case_number: 需要查询的案号。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个字典，包含裁判文书的相关信息。
    """

    def list_dict(input_data):
        if isinstance(input_data, dict) and "Items" in input_data:
            company_names = input_data["Items"]  # 直接从字典中获取'Items'键的值
        elif isinstance(input_data, list):
            company_names = input_data
        else:
            raise ValueError("Input must be a dict with an 'Items' key or a list.")
        return company_names

    case_number = case_number.replace("（", "(").replace("）", ")")

    # 使用list_dict函数处理need_fields参数
    need_fields = list_dict(need_fields) if need_fields is not None else []
    url = f"{domain}/law_api/s1_b/get_legal_document"
    data = {"query_conds": {"案号": case_number}, "need_fields": need_fields}
    try:
        rsp = requests.post(url, json=data, headers=headers)
        rsp.raise_for_status()  # 如果响应状态码不是200，将引发HTTPError异常
        return rsp.json()
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        return {}
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        return {}
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"OOps: Something Else: {err}")
        return {}


def glm4_create_case(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-0520",  # 填写需要调用的模型名称
            messages=messages,
        )
        if "```python" in response.choices[0].message.content:
            continue
        else:
            break
    return response


def get_answer_3(question):
    try:
        messages = [{"role": "user", "content": question}]
        response = glm4_create_case(2, messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None


def extract_case_number(case_number):
    prompt = f"请对以下案号进行规范化处理，并返回一个规范正确的案号,如(2021京01民初8641号规范化处理为(2021)京01民初8641号,2020皖1234民终9030号规范化处理为(2020)皖1234民终9030号。结果需以JSON格式返回，JSON结构应包含'案号'作为键，规范后的案号作为该键的值。请确保只返回JSON格式的字符串，不包含其他多余信息。\
期望输出（以JSON格式）:\
{{\"案号\":\"替换为实际规范后的案号\"}}\
现在请将案号{case_number}规范化处理\
    注意：\
1. 请确保输出的JSON字符串格式正确。\
2. '案号'是固定的键名，不需要替换或修改。"
    text = get_answer_3(prompt)
    # print('text',text)
    json_pattern = r"\{.*?\}"
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        # print('-------------------')
        json_string = match.group(0)
        # print(json_string)
        try:
            data = json.loads(json_string)
            return data["案号"]
        except json.JSONDecodeError:
            print("提取的字符串不是有效的JSON格式")
            return None
    else:
        print("在文本中没有找到匹配的JSON字符串")
        return None


def standardize_case_number(name):
    # 尝试直接获取注册名称
    registered_name = get_legal_document(name)
    if registered_name:
        return registered_name["案号"]  # 如果一开始就是注册名称，直接返回案号

    # 最多尝试5次标准化
    for attempt in range(5):
        # 尝试从名称中提取并解析案件编号
        result = extract_case_number(name)  # 假设这个函数已经被正确实现
        if result:
            # 更新名称为标准化后的结果
            name = result
            # 再次检查是否为注册名称
            registered_name = get_legal_document(name)
            if registered_name:
                # 如果找到了注册名称，停止循环并返回案号
                return registered_name["案号"]
        else:
            # 如果标准化失败（result为None或空），记录日志或进行其他处理
            print(f"Failed to extract case number from '{name}' on attempt {attempt + 1}")
            # 可以选择继续循环或提前退出

    # 如果循环结束仍未找到注册名称，返回原始名称或错误信息
    return (
        "此案号无案件"  # 或者抛出一个异常，如 raise ValueError("No registered name found for the given case number.")
    )


def extract_court_code(case_number):
    """
    从案号中提取法院代字及其后面的数字（0个、2个或4个），或只提取法院代字。

    参数:
    case_number (str): 单个案号字符串。

    返回:
    str: 包含案号对应的法院代字（及随后的数字，如果有的话）的字符串。
    """
    # 尝试匹配简称后跟0个、2个或4个数字
    match = re.search(
        r"([云京兵冀内军吉宁川新晋桂沪津浙渝湘琼甘皖粤苏藏豫赣辽鄂闽陕青鲁黑黔]\d{0,4}|最高法)", case_number
    )
    if match:
        return match.group(0)
    else:
        # 如果没有匹配到简称加数字或最高法，尝试只匹配简称
        match = re.search(r"([云京兵冀内军吉宁川新晋桂沪津浙渝湘琼甘皖粤苏藏豫赣辽鄂闽陕青鲁黑黔])", case_number)
        if match:
            return match.group(0)
        else:
            return None


if __name__ == "__main__":
    # 测试数据    正确获取代字
    case_numbers = [
        "(2021)最高法执1932号",
        "(2021)京01民初8641号",
        "(2020)皖1234民终9030号",
        "(特殊)沪",
        "浙",
        "(2022)浙01执123号",
        "(2023)黔0001执123号",
    ]
    # 调用函数并打印结果
    for i in case_numbers:
        print("转换测试：", extract_court_code(i))

    # 案号 大模型修正
    print(standardize_case_number("2020吉0184民初5156号"))

"""

法院代字({'云',
 '京',
 '兵',
 '冀',
 '内',
 '军',
 '吉',
 '宁',
 '川',
 '新',
 '晋',
 '最',
 '桂',
 '沪',
 '津',
 '浙',
 '渝',
 '湘',
 '琼',
 '甘',
 '皖',
 '粤',
 '苏',
 '藏',
 '豫',
 '赣',
 '辽',
 '鄂',
 '闽',
 '陕',
 '青',
 '鲁',
 '黑',
 '黔'})
"""
