# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 18:55:34 2024

@author: 86187
"""

import pandas as pd
import json
import datetime
import numpy as np

# 假设Excel文件名为'data.xlsx'且位于当前工作目录下
file_path = r"./prompt/ans_2.xlsx"

# 使用pandas读取Excel文件
df = pd.read_excel(file_path)
df = df[["id", "question", "answer"]]
# 将DataFrame转换为JSON格式的列表（每个字典代表一行数据）
data_list = df.to_dict(orient="records")


def replace_nan_with_empty_string(data_list):
    for item in data_list:
        if (
            "answer" in item and isinstance(item["answer"], float) and np.isnan(item["answer"])
        ):  # 只检查answer键，并且其值为None
            item["answer"] = ""
    return data_list


# 调用函数并打印结果
data_with_empty_strings = replace_nan_with_empty_string(data_list)

# 获取当前时间并格式化为字符串
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# 构建带有时间戳的文件名
file_name = f"data{timestamp}.json"
with open(file_name, "w", encoding="utf-8") as f:
    for item in data_with_empty_strings:
        # 将每个字典转换为JSON字符串并写入文件
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


# 写入到新的文件中，每个对象占一行
with open("./result.json", "w", encoding="utf-8") as f:
    for item in data_with_empty_strings:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
for i in range(200):
    print("------输出日志占位置----------")
print(len(data_with_empty_strings))
print("--------------打印输出结果-------------")
print(str(data_with_empty_strings[:50]))
print("--------------打印输出结果-------------")
print(str(data_with_empty_strings[50:100]))
print("--------------打印输出结果-------------")
print(str(data_with_empty_strings[100:150]))
print("--------------打印输出结果-------------")
print(str(data_with_empty_strings[150:]))
