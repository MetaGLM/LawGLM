from zhipuai import ZhipuAI
import tools
import run_v2
import template_look
import re
import json

client = ZhipuAI()


def find_json(text):
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        json_pattern = r"```json\n(.*?)\n```"
        match = re.search(json_pattern, text, re.DOTALL)
        if not match:
            json_pattern2 = r"({.*?})"
            match = re.search(json_pattern2, text, re.DOTALL)

        if match:
            json_string = match.group(1) if match.lastindex == 1 else match.group(0)
            try:
                # 移除Markdown格式的标记（如果存在）
                json_string = json_string.replace("```json\n", "").replace("\n```", "")
                data = json.loads(json_string)
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


# 调用glm4模型
def glm4_create_gh(messages):
    response = client.chat.completions.create(
        model="glm-4-plus",  # 填写需要调用的模型名称#GLM-4
        messages=messages,
    )
    # tools=tools)
    return response


def api_zhixing(content, tools):
    api_list = [
        "get_company_info",
        "get_company_register",
        "get_company_register_name",
        "get_sub_company_info",
        "get_sub_company_info_list",
        "get_legal_document",
        "get_legal_document_list",
        "get_court_info",
        "get_court_code",
        "get_lawfirm_info_log",
        "get_address_info",
        "get_address_code",
        "get_temp_info",
        "get_legal_abstract",
        "get_xzgxf_info",
        "get_xzgxf_info_list",
        "check_company",
        "func8",
        "function_11",
        "get_top_companies_by_capital",
        "check_restriction_and_max_amount",
        "calculate_total_amount_and_count_simple",
        "get_highest_legal_document_by_companyname",
    ]
    # Filter the tools based on the API functions mentioned in the response
    api_list_filter = [api for api in api_list if api in content]
    filtered_tools = [tool for tool in tools if tool.get("function", {}).get("name") in api_list_filter]
    print(api_list_filter)
    return api_list_filter, filtered_tools


# 多轮对话机制测试
def run_conversation_until_complete(messages, tools_all, max_rounds=8):
    last_response = None  # 用于存储最后一次对话的响应
    round_count = 0  # 对话轮数计数器
    response = glm4_create_gh(messages)

    while True:
        if round_count >= max_rounds:
            break  # 如果对话轮数超过最大值，则退出循环
        print(f"-------------------------第{round_count}对话-------------------")
        question = response.choices[0].message.content
        print(question)

        api_list_filter, filtered_tool = api_zhixing(question, tools_all)

        answer, function_result_logger = run_v2.get_answer_2(question, filtered_tool, False)
        print(str(function_result_logger))
        messages.append({"role": "assistant", "content": question})
        messages.append({"role": "user", "content": str(function_result_logger)})

        response = glm4_create_gh(messages)

        last_response = response.choices[0].message.content  # 存储最后一次响应

        if "全部完成" in response.choices[0].message.content:
            break  # 如果检测到“回答完成”，则停止循环

        round_count += 1  # 增加对话轮数计数

    return last_response  # 返回最后一次对话的内容


def way_string_2(question):
    way_string_2 = ">>解题参考："
    if "受理费" in question:
        way_string_2 += "查询受理费用时记得使用，get_legal_document(<填充需要查询的案号>,need_fields=['判决结果']));"
    if "涉案金额" in question and "高" in question and ("第" in question or "最" in question):
        way_string_2 += (
            "查询涉案金额最高或者第几高案件信息记得不使用function_11,优先使用get_highest_legal_document_by_companyname，\
            如果原告被告都查role就不设置，题目中没有明确指出需要被告还是原告就默认不设置role；如果查原告role设置问原告,如果查被告role就设置为被告\
            如最高可以设置get_highest_legal_document_by_companyname(<填充需要查询的案号>,n=1));\
    如被告涉案金额第二高可以设置get_highest_legal_document_by_companyname(<填充需要查询的案号>,role=被告,n=2));\
    如原告涉案第三高可以设置get_highest_legal_document_by_companyname(<填充需要查询的案号>,role=原告,n=3));"
        )

    if "中级人民法院" in question:
        way_string_2 += "特别注意 中级人民法院 案号中京01带有2位数字的才是中级人民法院，京不带数字的是高级人民法院，京0107带四个数字的是基层法院注意区分"
    if "基层" in question and "法院" in question:
        way_string_2 += "特别注意 最基层法院 就是案号中代字有四位数字的，如京0107就代表最基础法院"
    if "保留" in question and "小数" in question:
        way_string_2 += "特别注意 在总结答案前回答时确保保留小数位数一定要符合题意要求，题目保留1位小数，保留1位"
    if "限" in question and ("总额" in question or "总金额" in question):
        way_string_2 += (
            "特别注意 解题中限制高消费总额、次数优先使用函数calculate_total_amount_and_count_simple(<填充公司名称>)"
        )
    if "诉" in question and ("总额" in question or "总金额" in question):
        way_string_2 += "特别注意 解题中被起诉次数、金额优先使用函数function_11"
    if "子公司" in question and ("最高" in question or "最低" in question or "第" in question or "前" in question):
        way_string_2 += "特别注意 查询投资金额最高子公司或者最低子公司投资金额时，优先使用\
           get_top_companies_by_capital(company_name,rank_position=1)代表投资金额最高\
           get_top_companies_by_capital(company_name,rank_position=-1)代表投资金额最低"

    return way_string_2


def run_conversation_xietong(
    question,
):  # 核心代码   多智能体协调   多轮对话   先规划再执行，允许反馈一次错误，直到得到答案，限制8轮对话以内。
    file_path = "./prompt/promp_gh.txt"
    # Use a with statement to open the file
    with open(file_path, "r", encoding="utf-8") as file:
        content_p_1 = file.read()
    template_string, way_string = template_look.find_template_2(question)
    # with open('./prompt/way.txt', 'r', encoding='utf-8') as file:
    #      way_string = file.read()

    #  way_string='参考思路：' +way_string
    content_p = (
        content_p_1 + question + way_string + way_string_2(question)
    )  # +'参考思路：通过社会统一信用代码查询公司名称；通过公司名称查询全部涉案总次数；通过公司名称查询2020年作为被起诉人的涉案总次数及总金额。'
    print(content_p)
    file_path = "./prompt/promp_gh_2.txt"

    # Use a with statement to open the file
    with open(file_path, "r", encoding="utf-8") as file:
        content_p_2 = file.read()

    # template_string=template_look.find_template(question)  #启用模板模式
    # template_string='，例如：<全部完成，答案如下>：统一社会信用代码<填充>的公司全称是<填充>,该公司的涉案次数为<填充>次,（起诉日期在2020年）作为被起诉人的次数为<填充>次，（起诉日期在2020年）作为被起诉人的总金额为<填充,直接引用查询值，保留2为小数>'
    # template_string='，例如：<全部完成，答案如下>：主要答案总结要完整，如通过什么查到什么，再通过什么查到什么' #为空字符串不启用答题模板模式，自由答题
    # template_string='，例如：<全部完成，答案如下>：经查询，<填充>的审理日期为<填充>，该案件的原告律师事务所是<填充>，审理法院是<填充>，原告律师事务所地址为<填充>，审理法院地址为<填充>，原告律师事务所地址所在省份为<填充>，城市为<填充>，审理法院地址所在省份为<填充>，城市为<填充>，最低温度分别为<填充>度及<填充>度，最低温度相差<填充>度，本题使用的API个数为<填充>个，最小调用次数为<填充>次。'
    #'，例如：<全部完成，答案如下>：主要答案总结要完整，如通过什么查到什么，再通过什么查到什么'
    content_p_2 = content_p_2 + template_string

    print(content_p_2)
    tools_all = tools.tools_all
    # 执行函数部分
    messages = []

    messages.append({"role": "user", "content": "您好阿"})

    messages.append({"role": "user", "content": content_p})

    response = glm4_create_gh(messages)

    messages.append({"role": "assistant", "content": response.choices[0].message.content})

    messages.append({"role": "user", "content": content_p_2})  ###开始对话

    last_answer = run_conversation_until_complete(messages, tools_all, max_rounds=12)

    # print(run_conversation_until_complete(messages, tools_all, max_rounds=8))
    return last_answer, messages


def dict_to_formatted_string(data):
    try:
        if not isinstance(data, dict):
            raise ValueError("Input is not a dictionary")

        return ", ".join(f"{key}: {value}" for key, value in data.items())
    except Exception as e:
        print(f"dict_to_formatted_string执行时发生错误: {e}")
        return data  # 返回原始值


def run_conversation_tiqu(messages_1):
    messages = messages_1

    messages.append(
        {
            "role": "user",
            "content": '你不需要做总结了，根据上面内容，请把解决问题所使用到的字段，包括初始已知字段，直接以json呈现给我。\
                     如```json{ "公司代码": "300006","公司名称": "重庆莱美药业股份有限公司"}```',
        }
    )

    response = glm4_create_gh(messages)
    text_1 = response.choices[0].message.content
    """
        messages.append({"role": "assistant", "content":response.choices[0].message.content})
    
        messages.append({"role": "user", "content":content_p_2})  ###开始对话 
        
        
        last_answer=run_conversation_until_complete(messages, tools_all, max_rounds=10)
    """
    # print(run_conversation_until_complete(messages, tools_all, max_rounds=8))
    string1 = dict_to_formatted_string(find_json(text_1))
    return string1


def process_dict(d):
    # 检查输入是否为字典
    if not isinstance(d, dict):
        # 如果不是字典，则直接返回原值（假设它是一个字符串）
        return d
    # 检查字典中的每个键值对
    for key, value in d.items():
        # 如果值是一个字典，则递归调用此函数
        if isinstance(value, dict):
            return dict_to_formatted_string(value)
        # 如果值是一个字符串，则直接返回该字符串
        elif isinstance(value, str):
            return value


def run_conversation_psby(question):
    last_answer, messages_1 = run_conversation_xietong(question)
    print(last_answer)
    string_dict = find_json(last_answer)
    string_last = process_dict(string_dict)
    return string_last


if __name__ == "__main__":
    ques = "请问一下，浙江省丽水市景宁畲族自治县对应的区县登记的区划代码是？"
    # last_answer,messages_1=run_conversation_xietong(ques)
    # text=run_conversation_tiqu(messages_1)
    # print(messages_1)
    string_last = run_conversation_psby(ques)
    print("--------模型答案如下------------")
    print(string_last)
    # print(run_conversation_xietong(ques))

    # dict_to_formatted_string(find_json(last_answer))

    # find_json()
