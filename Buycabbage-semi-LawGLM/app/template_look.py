from zhipuai import ZhipuAI
import prompt.ans_template
import re
from Levenshtein import ratio
import pandas as pd
import numpy as np

client = ZhipuAI()

def find_muban(question_text):

    match = re.search(r"第(\d+)题", question_text)

    if match:
        # 如果找到了匹配项，则输出匹配到的数字
        number = match.group(1)
        print(f"找到的数字是: {number}")
        return number
    else:
        print("没有找到匹配的数字")
        return ""


# 调用glm4模型
def glm4_create_pick(messages):
    response = client.chat.completions.create(
        model="glm-4-plus",
        messages=messages,
    )

    total_tokens = response.usage.total_tokens

    print(total_tokens)
    print(f"----------totol_tokens{total_tokens}-------------")
    return response


def get_template_by_id(data_list, id_to_find):

    if not id_to_find:
        return "", ""

    try:
        search_id = int(id_to_find)
    except ValueError:
        return "", ""

    for item in data_list:
        if item["id"] == search_id:
            way_value = item.get("way", "")
            return item["template"], way_value

    return "", ""


def find_template(question):
    answer_template = prompt.ans_template.answer_template
    LLL = []
    for i in answer_template:
        if i["id"] not in [60, 61, 103, 126, 170, 181, 4, 24, 43, 166, 168, 176, 197, 199]:
            # print(i)
            if i["template"] != "":
                d = {"id": i["id"], "question": i["question"]}
                LLL.append(d)
    # print(LLL)

    pompt_pick = f"{LLL}我有上面这些题型。你要仔细分析思考，帮我查找哪个题型和问题:“{question}”类似，不用考虑案号，公司名称等差异？，回复样例：类似的题型是第id题。如果没找到，只回复没找到,不再做其他分析。"
    print(pompt_pick)
    # 执行函数部分
    messages = []
    # messages.append({"role": "system", "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分"})
    messages.append({"role": "user", "content": "您好阿"})

    messages.append({"role": "user", "content": pompt_pick})

    response = glm4_create_pick(messages)

    messages.append({"role": "assistant", "content": response.choices[0].message.content})

    # messages.append({"role": "user", "content":content_p_2})  ###开始对话

    muban_text = response.choices[0].message.content
    print(muban_text)
    #  find_muban(muban_text)
    muban_last, way_value = get_template_by_id(answer_template, find_muban(muban_text))
    # print(get_template_by_id(answer_template,find_muban(muban_text)))
    if muban_last:
        # muban_last='，例如：<全部完成，答案如下>：'+muban_last
        muban_last = f'如```json{ "<全部完成，答案如下>": muban_last}```'
    else:
        muban_last = '如```json{ "<全部完成，答案如下>":' "}```"
    if way_value:
        way_value = "参考思路：" + way_value

    else:
        way_value = ""

    return muban_last, way_value


def replace_nan_with_empty_string(data_list):
    for item in data_list:
        if (
            "template" in item and isinstance(item["template"], float) and np.isnan(item["template"])
        ):  # 只检查answer键，并且其值为None
            item["template"] = ""
        if (
            "way" in item and isinstance(item["way"], float) and np.isnan(item["way"])
        ):  # 只检查answer键，并且其值为None
            item["way"] = ""
    return data_list


def find_template_1(non_standard_name):
    # 假设这里有一个预定义的问题模板列表

    file_path = r"./prompt/ans_template_1.xlsx"

    # 使用pandas读取Excel文件
    df = pd.read_excel(file_path)
    df = df[["id", "question", "template", "way"]]
    # 将DataFrame转换为JSON格式的列表（每个字典代表一行数据）
    data_list = df.to_dict(orient="records")
    answer_template = replace_nan_with_empty_string(data_list)
    # answer_template =prompt.ans_template.answer_template
    # answer_template=data_list
    # 过滤掉特定ID的问题
    """
    standard_questions = [
        {'id': i['id'], 'question': i['question']}
        for i in answer_template
        if i['id'] not in [60, 61, 103, 126, 170, 181, 4, 24, 43, 166, 168, 176, 197, 199]
    ]
    
    LLL=[]
    for i in answer_template:
        if i['id'] not in [60,61,103,126,170,181,4,24,43,166,168,176,197,199]:
             #print(i)
             if i['template']!='':
                d= {'id': i['id'],'question':i['question']}               
                LLL.append(d)
    """
    standard_questions = answer_template

    # 定义一个函数来处理问题（如果需要的话）
    def process_question(question):
        # 如果需要对问题进行处理，比如去除某些词或标准化格式，可以在这里实现
        return question  # 目前不做任何处理

    # 处理标准问题列表
    processed_questions = [process_question(q["question"]) for q in standard_questions]

    # 使用Levenshtein的ratio函数找到最相似的问题
    best_match = max(processed_questions, key=lambda x: ratio(non_standard_name, x), default=None)

    # 如果找到了最佳匹配，则找到原始列表中的对应问题
    if best_match:
        original_best_match = next((q for q in answer_template if process_question(q["question"]) == best_match), None)

        muban_last = original_best_match.get("template", "")
        way_value = original_best_match.get("way", "")
        return original_best_match, muban_last, way_value
    else:
        return None


def find_template_2(question):
    _, muban_last, way_value = find_template_1(question)

    if muban_last:
        print(muban_last)
        # muban_last='，例如：<全部完成，答案如下>：'+muban_last
        muban_last = f'如```json{{"全部完成，答案如下": <引用模板填充,如,经查询,>}}```,模板：{muban_last}。还需注意模板供参照，如果问题和模板不完全对应，可以适当调整模板以更好回答问题。'
    else:
        muban_last = '如```json{{ "全部完成，答案如下":' "}}```"
    if way_value:
        way_value = "参考思路：" + way_value

    else:
        way_value = ""
    return muban_last, way_value


if __name__ == "__main__":
    """
    question='(2020)冀民终207号案件中，审理当天原告的律师事务所与被告的律师事务所所在地区的最高温度相差多少度？' 
    print(find_template(question))
"""
    # 示例使用
    question = (
        "2019年 湖北襄阳市中级人民法院民初1613号案原告方和原告律师事务所注册资本费别是？先成立的单位联系电话为？"
    )
    _, muban_last, way_value = find_template_1(question)

    print(_)
    print(find_template_2(question))
