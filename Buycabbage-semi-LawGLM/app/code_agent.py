# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 18:50:11 2024

@author: 86187
"""

from zhipuai import ZhipuAI
import requests
import json
from court_name_pre import to_standard_name
import company_name_glm4
import casenumber_pre


with open("api_key.txt", "r", encoding="utf-8") as file:
    api_key_string = file.read()

client = ZhipuAI(api_key=api_key_string)
# client = ZhipuAI(api_key="d5c3d44606e1a73a0c6cbcc32440f5fd.3vuwerg0G7xJvN4U")


domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",  # 团队token:D49……
}


# 6
def get_legal_document_list(related_company: str, need_fields: list = None):
    """
    根据关联公司查询所有裁判文书相关信息。
    参数:
    - related_company: 需要查询的关联公司名称。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个LegalDoc列表，包含与关联公司相关的所有裁判文书信息。
    """

    def list_dict(input_data):
        if isinstance(input_data, dict) and "Items" in input_data:
            company_names = input_data["Items"]  # 直接从字典中获取'Items'键的值
        elif isinstance(input_data, list):
            company_names = input_data
        else:
            raise ValueError("Input must be a dict with an 'Items' key or a list.")
        return company_names

    need_fields = list_dict(need_fields) if need_fields is not None else []
    url = f"{domain}/law_api/s1_b/get_legal_document_list"
    data = {"query_conds": {"关联公司": related_company}, "need_fields": need_fields}
    try:
        rsp = requests.post(url, json=data, headers=headers)
        rsp.raise_for_status()  # 如果响应状态码不是200，将引发HTTPError异常
        if need_fields:
            filtered_results = [{key: item[key] for key in need_fields if key in item} for item in rsp.json()]
        else:
            filtered_results = rsp.json()
        return filtered_results
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        return []
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        return []
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        return []
    except requests.exceptions.RequestException as err:
        print(f"OOps: Something Else: {err}")
        return []


# print(get_legal_document_list("创业慧康科技股份有限公司"))


# 调用glm4模型
def glm4_create_1(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-plus",  # 填写需要调用的模型名称
            messages=messages,
            # tools=tools,
        )
        print(attempt)
        if "```python" in response.choices[0].message.content:
            # 如果结果包含字符串'python'，则继续下一次循环
            continue
        else:
            # 一旦结果不包含字符串'python'，则停止尝试
            break
    # 检查最终的response是否仍然包含字符串'python'
    # if 'python' in response.choices[0].message.content:
    #  raise ValueError("最终响应中仍然包含字符串'python'")
    # 返回最终的response
    return response


def code_agent(question):
    try:
        messages = [{"role": "user", "content": question}]
        response = glm4_create_1(2, messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None


# 如果直接运行这个文件，则执行以下代码
if __name__ == "__main__":
    ques = "山西振东医药有限公司2019年被起诉次数及涉案总额为多少?"
    LL = get_legal_document_list("伊吾广汇矿业有限公司")
    question = f"{LL}，根据上述内容，如果涉及数量计算通过编写python代码计算后,请把列表全部内容传入计算，回答问题{ques},计算结果要符合题意，并列出全部案号，【注意】回答结果以json格式返回如{{涉案金额：}}"
    rsp = code_agent(question)
    print("回复：", rsp)

    import re

    data = {
        "关联公司": "山西振东医药有限公司",
        "标题": "山西振东医药有限公司与山东康伯中药饮片有限公司买卖合同纠纷执行裁定书",
        "案号": "(2021)晋0404执26号",
        "文书类型": "执行裁定书",
        # ...（其他字段保持不变）
        "日期": "2021-01-08 00:00:00",
        "文件名": "（2021）晋0404执26号.txt",
    }

    def add_case_year_and_rename_date(cases):
        # 检查cases是否为单个字典，如果是，则将其转换为列表
        if not isinstance(cases, list):
            cases = [cases]

        for case in cases:
            # 确保'案号'键存在
            if "案号" in case:
                # 从案号中提取年份
                match = re.search(r"\((\d{4})\)", case["案号"])
                if match:
                    case_year = match.group(1)
                    case["案件发生年度"] = case_year
                else:
                    case["案件发生年度"] = "未知"
            else:
                case["案件发生年度"] = "案号信息缺失"

            # 确保'日期'键存在
            if "日期" in case:
                case["审理日期"] = case.pop("日期")  # 更改键名并移除旧键
            else:
                # 如果'日期'键不存在，可以选择不添加'审理日期'键，或者设置为某个默认值
                # 这里选择不添加，但你可以根据需要调整
                pass

        # 如果输入是单个字典，则返回单个字典（如果需要）
        # if len(cases) == 1:
        #     return cases[0]

        return cases

    # 调用函数
    data = add_case_year_and_rename_date(data)

    # 打印修改后的数据以验证
    for case in data:
        print(case)
