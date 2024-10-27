# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 06:07:07 2024

@author: 86187
"""

import json


def json_to_data(path):
    data = []  # 初始化空列表来存储数据
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data_item = json.loads(line)
                data.append(data_item)
            except json.JSONDecodeError as e:
                print(f"Error decoding line: {line.strip()}")
                print(e)
        data = [{**obj, "answer": ""} for obj in data]
        return data


# questions_list=json_to_data('D:/zhipuAI/law_glm_复赛/submit-image-demo/tcdata/question_c.json')

"""
LLL=[]
for i in answer_template:
    if i['id'] not in [60,61,103,126,170,181,4,24,43,166,168,176,197,199]:
       d= {'id': i['id'],'question':i['question']}
       LLL.append(d)
#print(LLL)
       

import pandas as pd 
df=pd.DataFrame(answer_template)
df.to_excel('./prompt/ans_template.xlsx',index=False)
"""
