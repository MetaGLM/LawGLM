from knowledge.prompt import tip_prompt2
from Agent.llm import llm_eval
from knowledge.priori import TIPS
import re
from fuzzywuzzy import fuzz

def get_tips(question):
    messages = [{'role':'system','content':tip_prompt2},
                {'role': 'user', 'content': question+'\n\n请仅仅给出实体识别json'}]

    res = llm_eval(messages)
    ner = '以下是实体识别结果：\n'
    if '实体' in res and isinstance(res['实体'],list):
        for i in res['实体']:
            if i['格式匹配为'] !='公司名称':
                ner+=f"{i['名称']}为{i['格式匹配为']}\n"

    tips = ''
    for k, v in TIPS.items():
        if re.search(k, ner+question,re.DOTALL):
            tips += f'{v}\n'
    if tips:
        tips=f'以下是一般建议你需要根据题目内容来判断是否采纳：{tips}\n'


    return ner+tips,res



def filter_tip(question,ner):

    tip = ''
    if '实体' in ner and isinstance(ner['实体'],list):
        for i in ner['实体']:
            if i['格式匹配为'] not in ['公司名称','公司简称'] and fuzz.partial_ratio(i['名称'], question)>80:
                tip+=f"{i['名称']}为{i['格式匹配为']}\n"

    tips = ''
    for k, v in TIPS.items():
        if re.search(k, tip+question,re.DOTALL):
            tips += f'{v}\n'
    if tips:
        tips=f'以下是一般建议你需要根据题目内容来判断是否采纳：{tips}\n'

    if tip:
        tip = f'以下是实体识别结果：{tip}\n'

    return tip+tips