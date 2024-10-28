"""
Author: lihaitao
Date: 2024-07-05 12:34:40
LastEditors: Do not edit
LastEditTime: 2024-08-07 15:00:14
FilePath: /GLM2024/submit-image-demo/app/LLM.py
"""

from zhipuai import ZhipuAI
from prompt import *
import json
import re
import random

MAX_RETRY = 2

from tool_register.schema import database_schema


def LLM(query):
    client = ZhipuAI()
    response = client.chat.completions.create(
        model="glm-4-plus",
        messages=[
            {"role": "user", "content": query},
        ],
        stream=False,
        max_tokens=2000,
        do_sample=True,
    )
    return response.choices[0].message.content


# system_prompt = """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。
# 所提供的工具接口可以查询四张数据表的信息，数据表的schema如下:
# """ + database_schema
from zhipuai import ZhipuAI

tools = []


def LLMs_tools(query, tools):
    tools.append(
        {
            "type": "web_search",
            "web_search": {
                "enable": False  # 禁用：False，启用：True，默认为 True。
            },
        }
    )
    messages = [
        {
            "role": "system",
            "content": "你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。",
        },
        {"role": "user", "content": query},
    ]
    api_key = random.choice(API_KEY)
    client = ZhipuAI(api_key=api_key)
    # client = ZhipuAI(api_key=API_KEY)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                tools=tools,
                temperature=0,
                max_tokens=1500,
                do_sample=False,
                tool_choice="auto",
            )
            function = response.choices[0].message.tool_calls[0].function
            break
        except:
            api_key = random.choice(API_KEY)
            client = ZhipuAI(api_key=api_key)
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                tools=tools,
                temperature=0,
                max_tokens=1500,
                do_sample=True,
                tool_choice="auto",
            )
            function = response.choices[0].message.tool_calls[0].function

    # print("正在调用接口: ", function)

    func_args = function.arguments
    func_name = function.name
    return func_name, json.loads(func_args)


def prase_json_from_response(rsp: str):
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
    except json.JSONDecodeError as e:  # 因为太长解析不了
        try:
            match = re.search(r"\{(.*?)\}", rsp, re.DOTALL)
            if match:
                content = "[{" + match.group(1) + "}]"
                return json.loads(content)
        except:
            pass
        print(rsp)
        raise ("Json Decode Error: {error}".format(error=e))


def get_json_response(query, max_retries=MAX_RETRY):
    response = LLM(query)
    for retry in range(max_retries):
        try:
            response = LLM(query)
            # print(response)
            response = json.loads(response)
            return response
        except Exception as e:
            if retry == max_retries - 1:
                return None


def refine_answer(action, answer, other_result=""):
    prompt = f"""
    问题：{action}
    信息：{answer}
    其他信息：{other_result}
    请整合信息，直接给出和问题相关的简洁、完整且清晰的回答。回答格式忠于提问方式。不要回答问题之外的内容。
    如果信息中包含注册资本，注册资本单位为万元。
    答案要尽可能完整，包含问题中的所有关键内容。务必要完整回答问题并包含所有有效的观察结果。
    如果信息中存在报错信息，只保留报错信息帮助下一次迭代,不要额外输出指导解决办法。
    回答：
    """
    final_answer = LLM(query=prompt)
    return final_answer


def tongji_answer(question, answer):
    prompt = f"""
    问题：{question}
    信息：{answer}
    确定问题中需要统计的内容，准确无误的统计信息的相关信息作出回答。回答格式忠于提问方式。不要回答问题之外的内容。
    如果信息中列出的都是满足筛选条件的信息，请严格按照筛选后的内容作答。
    回答：
    """
    final_answer = LLM(query=prompt)
    return final_answer


def final_answer(question, answer):
    prompt = f"""
    问题：{question}
    解决路径：{answer}
    你是一个擅长综合答案的高级代理。请综合所有解决路径中的细致观察与分析，提炼出核心且有效的观察结果，以形成最终答案。
    1. 最终答案的呈现将严谨遵循题目设定的每一项要求，确保回答既全面又精确，不遗漏任何关键细节及有效的观察结果，力求完美契合题目期望。注意问题中的关键信息也要保留，以完整回答问题。
    2. 针对如涉案金额等具体数值的处理，若题目明确规定了小数点后的保留位数，我们将严格遵循这一要求，对相关金额进行精确无误的处理，确保数据的准确性。
    3. 答案的构建将全面覆盖解决路径中的每一个有效观察点，不仅直接给出最终答案，还将详尽展示答案探寻过程中的所有中间信息，包括但不限于律师事务所名称、法院全称、注册资本、成立日期、公司名称、案号、涉案金额等细节，以充分满足题目对于信息完整性严格要求。
    
    回答格式忠于提问方式。如果问题中存在案号，地址，公司名称，被告原告，统一社会代码等原始信息，务必要体现在最终回答中，以保证回答的完整性。
    请务必不要漏掉任何有效中间过程和观察结果内容！请务必不要漏掉任何有效中间过程和观察结果内容！务必注意问题中的关键信息也要保留，以完整回答问题。
    请不要除有效答案之外的无意义的说明，例如不要在答案中出现类似的说明：“以上答案严格遵循了题目要求的每一项细节，确保了信息的全面性和精确性。”
    回答格式要完整，要重述问题。
    
    问题：{question}
    解决路径：{answer}
    最终答案：
    """
    final_answer = LLM(query=prompt)
    return final_answer


# prompt = f"""
#     你是一个擅长整合API调用情况的高级代理。请根据提供的API调用情况，回答问题中关于API调用方面的问题。
#     注意只需要依据提供的API调用情况，回答问题中API调用方面的问题，其他问题不需要回答。
#     直接输出与原问题相关的最终答案，不要输出分析过程，不要输出多余信息。问题类型有如下四种：
#     1. API的调用次数（调用有几个）即为提供的所有步骤中API的调用次数总和。
#     2. API的串行调用次数（串行调用有几个）即为所有依赖于前序结果的API调用的次数，如果所有API调用都不依赖于前序结果，则串行调用次数为0次。
#     3. API的调用种类（调用有几类）即为提供的所有步骤中API的调用种类总和。（相同名称的API视为1种）。
#     4. API的串行调用种类（串行调用有几类）即为API串行调用链中的所有API的种类（相同名称的API视为1种），特别注意API串行调用链除了包括所有依赖于前序结果的API外，也需要包括位于首部、提供前序结果的API。
#     问题：{question}
#     API调用情况：{api_answer}
#     最终答案：


def rewrite_api_answer(api_answer):
    prompt = f"""
    你是一个擅长整合API调用情况的高级代理。请根据提供的API调用情况，回答关于API调用次数、串行调用次数、调用种类、串行调用种类方面的问题。
    直接输出最终答案，不要输出分析过程，不要输出多余信息。问题类型有如下四种：
    1. API的调用次数（调用有几个）即为提供的所有步骤中API的调用次数总和。
    2. API的串行调用次数（串行调用有几个）即为所有依赖于前序结果的API调用的次数，如果所有API调用都不依赖于前序结果，则串行调用次数为0次。
    3. API的调用种类（调用有几类）即为提供的所有步骤中API的调用种类总和。（相同名称的API视为1种）。
    4. API的串行调用种类（串行调用有几类）即为API串行调用链中的所有API的种类（相同名称的API视为1种），特别注意API串行调用链除了包括所有依赖于前序结果的API外，也需要包括位于首部、提供前序结果的API。 
    API调用情况：{api_answer}
    最终答案：
    """
    answer = LLM(query=prompt)
    return answer


def final_api_answer(question, answer, api_answer):
    # print("解决路径：", answer)
    rewrite_api = rewrite_api_answer(api_answer)

    prompt = f"""
    你是一个擅长综合答案的高级代理。请综合所有解决路径中的细致观察与分析，提炼出核心且有效的观察结果，以形成最终答案。
    
    1. 最终答案的呈现将严谨遵循题目设定的每一项要求，确保回答既全面又精确，不遗漏任何关键细节及有效的观察结果，保留所有有效实体。注意问题中的关键信息也要保留，以完整回答问题。
    2. 针对如涉案金额等具体数值的处理，若题目明确规定了小数点后的保留位数，我们将严格遵循这一要求，对相关金额进行精确无误的处理，确保数据的准确性。
    3. 答案的构建将全面覆盖解决路径中的每一个有效观察点，不仅直接给出最终答案，还将详尽展示答案探寻过程中的所有中间信息，包括但不限于律师事务所名称、审理法院名称，注册资本，成立日期及涉案金额等细节，以充分满足题目对于信息完整性严格要求。
    4. 对于API调用方面的答案，只需要回答次数和种类，不需要具体指出API的类别以及用途。

    如果问题中存在案号，地址，公司名称，被告原告信息，统一社会代码等原始信息，也要体现在最终回答中，以保证回答的完整性。
    请务必不要漏掉任何有效中间过程和观察结果内容！请务必不要漏掉任何有效中间过程和观察结果内容！
    请不要除有效答案之外的无意义的说明，例如不要在答案中出现类似的说明：“以上答案严格遵循了题目要求的每一项细节，确保了信息的全面性和精确性。”
    问题：{question}
    解决路径：{answer}
    API调用方面的答案：{rewrite_api}
    最终答案：
    """
    final_answer = LLM(query=prompt)
    return final_answer


def simplify_answer(answer):
    prompt = f"""
    你是一个擅长整理答案的高级代理，给定一份答案，你的任务是在保持答案有效性和完整性的前提下，对答案进行去重，从而确保答案的有效性和简洁性。
    
    1. 有效性：务必要全面精确地保留答案的信息，不遗漏任何关键细节及有意义的表述，保留答案中所有的有效实体，包括但不限于律师事务所名称、法院全称、注册资本、成立日期、公司名称、案号、涉案金额等细节。
    2. 简洁性：去除答案中重复的表述，避免信息冗余。特别地，如果答案在结尾出现了总结（通常有关键词: "故,因此,最终答案为,最终答案如下"等），应当判断结尾总结是否增加了有效信息，如果结尾总结的信息在前述部分已经出现过并且没有新的分析加工，则需要删除末尾的重复总结部分。
    
    输出忠于答案原内容，不要添加任何额外内容。    
    答案：{answer}
    输出：
    """
    final_answer = LLM(query=prompt)
    return final_answer


# def get_final_answer(question, sub_query, sub_answer):
#     prompt=f"""
#     请整合子问题答案，给出原问题的最终答案。。
#     原问题：{question}
#     子问题：{sub_query}
#     子答案：{sub_answer}

#     回答：
#     """
#     final_answer = LLM(query=prompt)
#     return final_answer
