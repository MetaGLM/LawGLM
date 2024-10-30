# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 19:16:25 2024

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
    "Authorization": "Bearer black_myth_wukong",  # 团队token:D49……
}


def get_company_register(company_name: str, need_fields: list = None) -> dict:
    """
    根据公司名称查询对应的注册信息。
    参数:
    - company_name: 需要查询的公司名称。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个字典，包含公司对应的注册信息。
    """

    # 此处假设您已经有了一个名为list_dict的函数来处理need_fields参数，如同您提供的get_address_info函数中那样。
    def list_dict(input_data):
        if isinstance(input_data, dict) and "Items" in input_data:
            company_names = input_data["Items"]  # 直接从字典中获取'Items'键的值
        elif isinstance(input_data, list):
            company_names = input_data
        else:
            raise ValueError("Input must be a dict with an 'Items' key or a list.")
        return company_names

    # 使用list_dict函数处理need_fields参数
    need_fields = list_dict(need_fields) if need_fields is not None else []

    url = f"{domain}/law_api/s1_b/get_company_register"
    data = {"query_conds": {"公司名称": company_name}, "need_fields": need_fields}
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


def get_company_info(query_conds: dict, need_fields: list = None) -> dict:
    """
    根据上市公司名称、简称或代码查找上市公司信息。
    参数:
    - query_conds: 查询条件字典，包含公司名称、简称或代码。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个字典，包含上市公司的相关信息。
    """

    # 使用list_dict函数处理need_fields参数
    def list_dict(input_data):
        if isinstance(input_data, dict) and "Items" in input_data:
            company_names = input_data["Items"]  # 直接从字典中获取'Items'键的值
        elif isinstance(input_data, list):
            company_names = input_data
        else:
            raise ValueError("Input must be a dict with an 'Items' key or a list.")
        return company_names

    need_fields = list_dict(need_fields) if need_fields is not None else []
    url = f"{domain}/law_api/s1_b/get_company_info"
    data = {"query_conds": query_conds, "need_fields": need_fields}
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


def get_legal_document_list_checkname(company_name: str) -> dict:
    url = f"{domain}/law_api/s1_b/get_legal_document_list"
    data = {"query_conds": {"关联公司": company_name}, "need_fields": []}
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


def glm4_create(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-plus",  # 填写需要调用的模型名称
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
        response = glm4_create(2, messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None


def extract_and_parse_json(question):
    prompt = f"有的公司名称经常会多写一些字或者遗漏一些字，有的多谢了一些叠词，例如上海市妙可蓝多食品科技股份有限公司，规范名称是上海妙可蓝多食品科技股份有限公司，如信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司,范名称是信息产业电子第十一设计研究院科技工程股份有限公司\
        参考上述背景请对以下公司名称{question}进行规范化处理，并返回一个规范正确的公司名称。结果需以JSON格式返回，JSON结构应包含'公司名称'作为键，规范后的公司名称作为该键的值。\
        请确保只返回JSON格式的字符串，不包含其他多余信息。\n期望输出（以JSON格式）:\n{{\"公司名称\":\"替换为实际规范后的公司名称\"}}\n注意：\n1. 请将{question}替换为实际要规范化的公司名称。\n2. 请确保输出的JSON字符串格式正确。\n3. '公司名称'是固定的键名，不需要替换或修改。"
    text = get_answer_3(prompt)
    #    print(text)
    json_pattern = r"\{.*?\}"
    match = re.search(json_pattern, text)
    if match:
        json_string = match.group(0)
        try:
            data = json.loads(json_string)
            return data["公司名称"]
        except json.JSONDecodeError:
            print("提取的字符串不是有效的JSON格式")
            return None
    else:
        print("在文本中没有找到匹配的JSON字符串")
        return None


def standardize_company_name(name):
    registered_name = get_company_register(name)
    if not registered_name:
        for i in range(10):  # 设置最大尝试次数为5
            result = extract_and_parse_json(name)
            if result:  # 如果标准化成功
                name1 = result  # 更新名称为标准化后的结果
                # print('------------')
                # print(registered_name)
                registered_name = get_company_register(name1)  # 再次检查是否为注册名称

                if registered_name:  # 如果找到了注册名称，停止循环并返回
                    break
            else:
                return f"无法标准化公司名称{name}"  # 如果标准化失败，返回失败信息
        if registered_name:  # 如果循环结束后找到了注册名称，返回注册名称
            return registered_name["公司名称"]
        else:
            return f"无法标准化公司名称{name}"  # 如果循环结束仍未找到注册名称，返回失败信息
    else:
        return name  # 如果一开始就是注册名称，直接返回


def standardize_company_name_1(name):
    registered_name = get_legal_document_list_checkname(name)
    # print(registered_name)
    if not registered_name:
        for i in range(5):  # 设置最大尝试次数为5
            result = extract_and_parse_json(name)
            if result:  # 如果标准化成功
                name1 = result  # 更新名称为标准化后的结果
                # print('------------')
                # print(registered_name)
                registered_name = get_company_register(name1)  # 再次检查是否为注册名称

                if registered_name:  # 如果找到了注册名称，停止循环并返回
                    break
            else:
                return f"无法标准化公司名称{name}"  # 如果标准化失败，返回失败信息
        if registered_name:  # 如果循环结束后找到了注册名称，返回注册名称
            return registered_name["公司名称"]
        else:
            return name  # 如果循环结束仍未找到注册名称，返回失败信息
    else:
        return name  # 如果一开始就是注册名称，直接返回


def check_listed_company(company_name):
    # 先执行a函数
    company_name = standardize_company_name(company_name)
    a_result = get_company_register(company_name)
    # print(a_result)
    # 判断a函数的结果
    if a_result:
        # a函数有结果，继续执行b函数
        b_result = get_company_info(query_conds={"公司名称": a_result["公司名称"]}, need_fields=[])

        # 判断b函数的结果
        if b_result:
            # a和b函数都有结果，是上市公司
            return {
                "公司名称": company_name,
                "是否为上市公司": "是。在上市公司表获得了信息",
            }
        else:
            # a有结果但b没有结果，不是上市公司
            return {"公司名称": company_name, "是否为上市公司": "否。工商表有信息，但在上市公司表未获得信息"}
    else:
        # a函数没有结果，不是上市公司
        return {
            "公司名称": company_name,
            "是否为上市公司": "否。工商信息表，上市公司信息表均无信息，请确认公司名称是否正确",
        }


# 如果直接运行这个文件，则执行以下代码
if __name__ == "__main__":
    company_name = "温洲明鹿基础设施投资有限公司"
    standard_name = standardize_company_name(company_name)
    print("大模型规范化的公司名称是：", standard_name)
"""    
    #check1=check_listed_company('北京市三元食品股份有限公司')
   # print(check1)
    company_name = '信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司'
    standard_name = standardize_company_name_1(company_name)
    print("大模型规范化的公司名称是：", standard_name)
"""
