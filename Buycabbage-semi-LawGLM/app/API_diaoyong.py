from zhipuai import ZhipuAI
import re
import json


client = ZhipuAI()

domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",  # 团队token:D49……
}


def glm4_create_diaoyong(max_attempts, messages):
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


def find_json(text):
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        json_pattern = r"```json\n(.*?\n)```"
        match = re.search(json_pattern, text, re.DOTALL)

        # 如果第一个模式没有匹配到内容
        if not match:
            # 使用第二个正则表达式尝试匹配，这个模式更通用，不包含Markdown特定的标记
            json_pattern2 = r"({.*?})"
            match = re.search(json_pattern2, text, re.DOTALL)

        if match:
            json_string = match.group(1) if match.lastindex == 1 else match.group(0)
            try:
                # 移除Markdown格式的标记（如果存在）
                json_string = json_string.replace("```json\n", "").replace("\n```", "")
                data = json.loads(json_string)
                print("匹配成功啦")

                return data
            except json.JSONDecodeError as e:
                if attempt < max_attempts:
                    print(f"Attempt {attempt}: Failed to parse JSON, reason: {e}. Retrying...")
                else:
                    print(f"All {max_attempts} attempts to parse JSON failed. Giving up.")
        else:
            if attempt < max_attempts:
                print(f"Attempt {attempt}: No JSON string found in the text. Retrying...")
            else:
                print("No matching JSON string found in all attempts.")
        return text


"""

def API_count_agent(question, answer,API_l):
    
    if '串行' in question:
        
        
        LL=API_l
        api_lei=len(set(LL))
        api_cx=len(set(LL))-1
        d={'API串行次数':f'{api_cx}次','API类别':f'{api_lei}类'}
        audit_prompt = f"问题：'{question}' , 答案：'{answer}' ,根据正确结果{d}，修改答案,只局部修改正确结果有关内容,其余保持答案原文不变，返回修改后的答案,以json格式返回,如```json\n{{answer:.....}}\n```"
        print(audit_prompt )
        messages = [{"role": "user", "content": audit_prompt}]
        response = glm4_create_diaoyong(1, messages)  
        content = response.choices[0].message.content.strip()
        answer1=find_json(content )
        #print(answer1['answer'])
        return answer1['answer']
    else:
        
        return answer
"""


def API_count_glm(question):
    # Specify the file path
    file_path = "./API_diaoyong.txt"

    # Use a with statement to open the file
    with open(file_path, "r", encoding="utf-8") as file:
        content_p = file.read()
    audit_prompt = (
        content_p
        + f"我有上面17类API，通过调用API一步一步回答问题'{question}' ,请告诉我解答这个问题调用了几类API，串行了几次。串行概念:从通过一个API获得结果再去调用另一个API才算串行一次,通过问题已知内容调用api不算串行。调用几类API概念:解答问题使用不同api的个数。你自己详细思考分析，回复要简洁，不做无关回答，例如：调用了API3次"
    )

    messages = [{"role": "user", "content": audit_prompt}]
    response = glm4_create_diaoyong(1, messages)
    content = response.choices[0].message.content.strip()
    # print(content)
    return content


def API_diaoyong_agent(question, answer):
    if "串行" in question or "调用" in question:
        # print('123')

        d = API_count_glm(question)
        audit_prompt = f"我有一个问题和答案，这个答案关于API串行调用部分回答不正确。正确的分析结果如下{d}。\
请根据正确的结果数量修改答案，只修改答案中与‘调用’、‘串行’相关内容，其余保持答案原文不变。\
问题：'{question}'，需要修正的答案：'{answer}'。\
【注意】只修改问题中问到的串行、调用次数，问题中没有问到串行就不必回答串行，次数要使用1次，2次，3次，记得带上单位，问题中问什么单位回答就用什么单位，只修改答案中不对部分其余保持答案原文不变，并确保完整且准确地回答问题，不做其他无关的回答。\
返回json格式，如```json\n{{修正后答案: }}\n```"
        # print(audit_prompt )
        messages = [{"role": "user", "content": audit_prompt}]
        response = glm4_create_diaoyong(1, messages)
        content = response.choices[0].message.content.strip()
        answer1 = find_json(content)
        # print(answer1)
        # 检查变量是否为字典
        if isinstance(answer1, dict):
            # 获取字典中的值
            answer1 = answer1["修正后答案"]
        else:
            answer1 = (
                answer1.replace("```json\n", "")
                .replace("\n```", "")
                .replace("修正后答案:", "")
                .replace('{ "', "")
                .replace('"}', "")
            )
        return answer1
    else:
        return answer


if __name__ == "__main__":
    answer = "安徽安科恒益药业有限公司的注册地址位于安徽省铜陵市经济开发区新城区，该地址对应的区县为铜官区。"
    ques = "安徽安科恒益药业有限公司注册地址所在区县是？API的ci数为？"
    print(API_diaoyong_agent(ques, answer))
