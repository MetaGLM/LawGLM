# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 09:25:41 2024

@author: 86187
"""

from zhipuai import ZhipuAI
import pandas as pd
import numpy as np
from Levenshtein import ratio

client = ZhipuAI()

domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",
}


def glm4_create_audit(max_attempts, messages):
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


# 调用glm4模型
def glm4_create_model_ensembling(messages):
    response = client.chat.completions.create(
        model="glm-4-plus",  # 填写需要调用的模型名称#GLM-4
        messages=messages,
    )
    # tools=tools)

    total_tokens = response.usage.total_tokens

    # print(total_tokens)
    # print(f'----------totol_tokens{total_tokens}-------------')
    return response


def audit_agent(question, answer, max_retries=2):
    """
    Audits if the given answer completely addresses the question using an AI model,
    expecting a judgment on the completeness of the answer, with retries on ambiguous replies.

    :param question: The original question to be evaluated.
    :param answer: The answer to be audited for its completeness.
    :param max_retries: Maximum retry attempts for unclear responses.
    :return: True if the answer is deemed complete, False otherwise, or None on max retries.
    """
    audit_prompt = f"评估问题：'{question}' 和 答案：'{answer}' 是否匹配。如果答案完全解决了问题，回复'是'；如果答案不完整、未找到信息或需要更多信息，请回复'否'。"
    for attempt in range(max_retries + 1):
        try:
            messages = [{"role": "user", "content": audit_prompt}]
            response = glm4_create_audit(2, messages)
            content = response.choices[0].message.content.strip()
            print(content)

            # 更精确的判断逻辑
            if (
                    "没有查询到" in content
                    or "不正确" in content
                    or "没有公开" in content
                    or "未能" in content
                    or "否" in content
                    or "没有" in content
            ):
                return False
            elif "是" in content:
                return True
            else:  # 如果不是预期的简单回答，则根据内容逻辑判断
                if (
                        "没有查询到" in content
                        or "不正确" in content
                        or "没有公开" in content
                        or "未能" in content
                        or "否" in content
                ):
                    return False
                else:  # 如果内容依然不清晰，决定是否重试
                    # print(f"收到非预期回复：'{content}', 正在重试...")
                    continue

        except Exception as e:
            # if attempt < max_retries:
            # print(f"第{attempt+1}/{max_retries+1}次尝试失败，错误原因：{e}")
            # else:
            # print(f"经过{max_retries}次尝试，未能获得明确答复，最后一次错误：{e}")
            continue

    return False


def replace_nan_with_empty_string(data_list):
    for item in data_list:
        if (
                "answer" in item and isinstance(item["answer"], float) and np.isnan(item["answer"])
        ):  # 只检查answer键，并且其值为None
            item["answer"] = ""

    return data_list


def find_template_ans(non_standard_name):
    # 假设这里有一个预定义的问题模板列表

    file_path = r"./prompt/ans_2.xlsx"

    # 使用pandas读取Excel文件
    df = pd.read_excel(file_path)
    df = df[["id", "question", "answer"]]
    # 将DataFrame转换为JSON格式的列表（每个字典代表一行数据）
    data_list = df.to_dict(orient="records")
    answer_template = replace_nan_with_empty_string(data_list)
    # answer_template =prompt.ans_template.answer_template
    # answer_template=data_list
    # 过滤掉特定ID的问题

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

        ans_2 = original_best_match.get("answer", "")

        return ans_2
    else:
        return ""


def audit_agent_model_ensembling(question, ans_a):
    messages = []

    messages.append({"role": "user", "content": "您好阿"})

    ans_b = find_template_ans(question)

    promt = f"你现在做选择题，我在回答问题{question} 答案A：{ans_a} 答案B:{ans_b}哪个答案更加全面完整更好地回答题，如果没查询到则是比较差的答案。请告诉我哪个答案更好，A或者B，不要返回其他内容只返回你的选择。"

    messages.append({"role": "user", "content": promt})

    response = glm4_create_model_ensembling(messages)

    if "A" in response.choices[0].message.content:
        ans_last = ans_a
    else:
        ans_last = ans_b
    return ans_last


def audit_agent_model_ensembling_1(question, ans_a, ans_b, ans_c):
    messages = []

    messages.append({"role": "user", "content": "您好阿"})

    # ans_b=find_template_ans(question)

    promt = f"你现在做选择题，我在回答问题{question} ，获得了三个答案，\
        答案A：{ans_a} ,\
        答案B:{ans_b},\
        答案C:{ans_c}\
        哪个答案更加全面完整更好地回答题，如果没查询到则是比较差的答案。\
        请告诉我哪个答案更好，更好的查询到了与问题有关的信息，A或者B或者C，\
        不要返回其他内容只返回你的选择。"
    print(promt)
    messages.append({"role": "user", "content": promt})

    response = glm4_create_model_ensembling(messages)

    if "A" in response.choices[0].message.content:
        print("-----------选择A------------")
        ans_last = ans_a
    elif "B" in response.choices[0].message.content:
        print("-----------选择B------------")
        ans_last = ans_b
    else:
        print("-----------选择C------------")
        ans_last = ans_c
    return ans_last


if __name__ == "__main__":
    question_a = "统一社会信用代码是91370000164102345T这家公司的法人是谁"
    answer_a = "这家公司的法定代表人是琇。hhhh"
    answer_b = "这家公司的法定代表人是小琇。"
    answer_c = "这家公司的法定代表人是不知道。"
    # 调用修改后的函数进行测试
    rsp = audit_agent_model_ensembling_1(question_a, answer_a, answer_b, answer_c)
    print(rsp)  # 应该输出 False，因为答案表明没有查到所需信息
