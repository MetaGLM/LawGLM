# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 06:52:38 2024

@author: 86187
"""

import requests
import pandas as pd
from Levenshtein import ratio


domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",  # 团队token:D49……
}


def http_api_call_test(api_name, data, max_data_len=None):
    url = f"{domain}/law_api/s1_b/{api_name}"
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp
    if max_data_len is None:
        max_data_len = len(final_rsp)

    return final_rsp


def get_court_code_test(courtname):
    data1 = {"query_conds": {"法院名称": courtname}, "need_fields": []}
    api_name = "get_court_code"
    return http_api_call_test(api_name, data1)


# 假设您有一个规范的法院名录列表
def to_standard_name_1(non_standard_name):
    df = pd.read_excel("法院名录库.xlsx")
    LL = list(df["法院名称"])
    standard_courts = LL
    non_standard_name = non_standard_name

    # 定义一个函数来处理字符串，移除“人民法院”
    def process_court_name(name):
        return name.replace("人民法院", "") if "人民法院" in name else name

    # 处理standard_courts列表中的每个元素
    processed_courts = [process_court_name(court) for court in standard_courts]

    # 使用Levenshtein的ratio函数进行匹配
    best_match = max(processed_courts, key=lambda x: ratio(non_standard_name.replace("法院", ""), x), default=None)

    # 注意：如果best_match是处理后的字符串，您可能需要找到原始列表中的对应项
    if best_match:
        # 查找原始列表中的对应项
        original_best_match = next(
            (court for court in standard_courts if process_court_name(court) == best_match), None
        )
        # print(original_best_match)
    # else:
    # print("没有找到匹配项")
    return original_best_match


def to_standard_name(courtname):
    # aa=get_court_code_test(courtname)
    # print(aa)
    if get_court_code_test(courtname):
        #  print('2333')
        return courtname
    else:
        courtname = to_standard_name_1(courtname)
        return courtname


if __name__ == "__main__":
    non_standard_name = "丰台法院"
    non_standard_name = "大邑县人民法院"
    print(to_standard_name(non_standard_name))
