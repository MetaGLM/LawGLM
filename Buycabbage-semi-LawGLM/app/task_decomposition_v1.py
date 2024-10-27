import json

from zhipuai import ZhipuAI
import re
import run_v2
import API_diaoyong
import tools
import API_look1

client = ZhipuAI()


need_fields = []
domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 3BC078EB97F78FB2ABC6B2825A1FE57F783DF2BEE85336CC",  # 团队token:D49……
}


def glm4_create_fj(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-0520",  # 填写需要调用的模型名称
            messages=messages,
        )
        if "python" in response.choices[0].message.content:
            continue
        else:
            break
    return response


def get_answer_4(question):
    try:
        messages = [{"role": "user", "content": question}]
        response = glm4_create_fj(2, messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None


# tool_1=run_v2.tools


def extract_and_parse_json(question):
    # 我有这些工具{tool_1}\

    prompt = f'\
         参考问题1："原告是安利股份的案件审理法院是哪家法院"，问题可以分解改写样例{{问题一：通过公司简称<安利股份>查询<公司名称>，问题二：通过公司名称查询为原告的案号，问题三：通过案号查询法院名称}}\
        \参考问题2："某某公司涉案金额最高的法院的负责人是？"，问题可以分解改写样例{{问题一：调用get_legal_document_list,通过公司名称<某某>查询案号、涉案金额，问题二：从获得数据中根据涉案金额判断出涉案金额最高的案号,问题三：调用get_court_info_code,根据案号获得法院负责人}}\
        \参考问题3："(2019)晋1026民初704号案件中的原告事务所服务过多少家上市公司？"，问题可以分解改写样例{{问题一：通过案号<(2019)晋1026民初704号>查询原告事务所名称，问题二：通过获取的事务所名称查询服务过多少家上市公司}}\
        \参考问题4："妙可蓝多注册在哪个市的哪个区？"，问题可以分解改写样例{{问题一：通过公司简称妙可蓝多查询注册地址，问题二：通过注册地址查询省份城市区县}}\
        \参考问题5："原告是300077案件审理法院是什么时候成立的？"，问题可以分解改写样例{{问题一：通过公司代码300077查询公司名称，问题二：通过公司名称查询该公司为被告的案号,问题三：通过案号查询审理法院名称、成立日期}}\
        \参考问题6："某某公司投资金额最高的子公司是？投资金额是？法定代表人、成立日期、统一社会信用代码分别是什么？"，问题可以分解改写样例{{问题一：通过公司名称查询特定条件子公司名称、投资金额，问题二：通过获得的公司名称查询该公司法定代表人、成立日期、统一社会信用代码}}\
        \参考问题6："安利股份的子公司的一级行业是什么？"，问题可以分解改写样例{{问题一：通过公司简称安利股份查询公司名称，问题二：通过公司名称查询子公司名称，问题三：通过子公司的公司名称查询一级行业}}\
        \参考问题7："山西振东医药贸易有限公司的统一社会代码是？注册资本是多少亿元？请保留三位小数。该公司的涉案次数为？作为被起诉人的次数为？？"，问题可以分解改写样例{{问题一：通过公司名称查询山西振东医药贸易有限公司的统一社会信用代码，问题二：通过公司名称查询山西振东医药贸易有限公司的注册资本，问题三：通过公司名称查询山西振东医药贸易有限公司的涉案次数 建议调用function_11, 问题四: 通过公司名称查询山西振东医药贸易有限公司作为被起诉人的次数 建议function_11}}\
        \参考问题8："某某公司涉及的案件中，起诉时间发生于2020年发生的民事初审或执行案件有几次？案号分别是？"，问题可以分解改写样例{{问题一：通过公司名称某某公司查询2020年发生的民事初审或执行案件次数、涉案金额综合、案号}}\
        \参考问题9："上海妙可蓝多食品科技股份有限公司的地址在哪里？该公司被限告的涉案总额为？总数为？"，问题可以分解改写样例{{问题一：通过公司名称查询上海妙可蓝多食品科技股份有限公司的地址，问题二:通过公司名称查询上海妙可蓝多食品科技股份有限公司被限高的涉案总金额、涉案次数}}\
        \参考问题10："(2019)川01民初1949号关联公司的注册地址在哪，该案的法院地址又在哪里，包括原告律师事务所所在的地址在内，这三个地址分别分布在几个省级行政区？"，问题可以分解改写样例{{问题一：通过案号(2019)川01民初1949号查询关联公司名称，问题二：通过公司名称查询注册地址，问题三:通过案号<(2019)川01民初1949号>查询审理该案的法院地址，问题四: 通过案号<(2019)川01民初1949号>查询原告律师事务所名称，问题五：通过律师事务所名称查询律师事务所地址,问题六：三个地址分别分布在几个省级行政区\'}}\
        \参考问题11："12345678910F的公司全称是？该公司的涉案次数为？（起诉日期在2020年）作为被起诉人的次数及总金额为？"，问题可以分解改写样例{{问题一：通过统一社会信用代码<12345678910F>查询公司名称，问题二：通过公司名称查询全部涉案次数，问题二：通过公司名称查询2020年作为被告的涉案次数和涉案金额\'}}\
        \参考问题12："（2019）粤0305民初1818号被告所请的律师事务所的登记机关是？"，问题可以分解改写样例{{问题一：通过案号（2019）粤0305民初1818号查询被告律师事务所名称，问题二：通过律师事务所名称查询律师事务所登记机关\'}}\
        \参考问题13："上海晨光文具股份有限公司投资的圈资公司有哪些？投资金额分别为？"，问题可以分解改写样例{{问题一：通过公司名称上海晨光文具股份有限公司查询投资的全资子公司，投资金额，get_sub_company_info_list 参数only_wholly_owned: bool =True\'}}\
         \参考问题14："上海东方华银律师事务所服务已上市公司的数量是多少家？"，问题可以分解改写样例{{问题一：通过上海东方华银律师事务所事务所名称查询服务过多少家上市公司}}\
        \按照分解改写样例，分解改写新问题：“{question}”，以json格式返回,如```json\n{{问题一: ,问题二:,问题三:.....}}\n```'

    """
    # 指定文件路径
    file_path = './prompt.txt'
        # 使用with语句打开文件，这种方式不需要手动关闭文件
    with open(file_path, 'r', encoding='utf-8') as file:
        # 读取文件内容
        content_p = file.read()
        # 打印文件内容
    prompt=content_p+f"我想查询{question},请您参考样例一步一步按照给定API分解问题，以json格式返回,如```json\n{{问题一:<填充> ,问题二:<填充>,问题三:<填充>}}\n```"
    print(prompt)
    print('------------------------')
    """
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        text = get_answer_4(prompt)
        # print('-----------------text----------------')
        # print(text)
        # print('---------------text-----------------')
        json_pattern = r"```json\n{.*?\}\n```"
        match = re.search(json_pattern, text, re.DOTALL)

        # 如果第一个模式没有匹配到内容
        if not match:
            # 使用第二个正则表达式尝试匹配，这个模式更通用，不包含Markdown特定的标记
            json_pattern2 = r"{.*?}"
            match = re.search(json_pattern2, text, re.DOTALL)
        if match:
            json_string = match.group(0)
            try:
                json_string = json_string.replace("```json\n", "").replace("\n```", "")
                # print(json_string)
                data = json.loads(json_string)
                return data
            except json.JSONDecodeError as e:
                if attempt < max_attempts:
                    print(f"尝试 {attempt} 解析JSON失败，原因：{e}, 将再次尝试...")
                else:
                    print(f"尝试 {max_attempts} 次解析JSON均失败，最终放弃。")
        else:
            if attempt < max_attempts:
                print(f"尝试 {attempt} 在文本中未找到JSON字符串，将再次尝试...")
            else:
                print("所有尝试中均未在文本中找到匹配的JSON字符串。")
    return None


def find_json(text):
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        json_pattern = r"```json\n(.*?)\n```"
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


def beijing(ques_zhu, LL, v, tools):
    print(tools)
    prompt = f"我已经掌握的问题背景如下{LL},根据背景中答案组织语言回答问题:{v}?，请调用工具查询"  # ，【注意】答案必须以json格式返回，如```json\n{{答案:}}\n```

    text, function_result_logger = run_v2.get_answer_2(prompt, tools, api_look=False)

    if not isinstance(text, str):
        raise ValueError("Expected a string object, got {}".format(type(text)))
    # text1=find_json(text)
    return text, function_result_logger


def wenti_youhua(LL, v):
    # prompt = '参考问题：“原告是安利股份的案件审理法院是哪家法院”，问题可以分解改写样例“{问题一：通过安利股份查询公司名称，问题二：通过公司名称查询原告和案号，问题三：通过案号查询法院名称}” 请按照分解改写样例，分解改写新问题：“原告是中持股份的案件审理法院是哪家法院"”，以json格式返回'
    if "位小数" in v:
        promt_bl = "[注意]请仔细核对金额，确保精确到小数位数符合题意要求。无需添加千位分隔符，例如，金额是3,724,384.07，应紧凑回答为：3724384.07。请务必保留正确的小数位数。”"
        prompt = f"查询到结果：{LL},根据查询结果请回答问题{v},答案语言流畅准确，参考样例答题风格。" + promt_bl
    else:
        prompt = f"查询到结果：{LL},根据查询结果请回答问题{v},答案语言流畅准确，答案尽量引用查询到结果中键和值。参考样例答题风格。【注意】如果遇到数值，无需添加千位分隔符，例如，金额是3,724,384.07，应紧凑回答为：3724384.07。"
        # prompt = f"将列表中内容{LL}变成流畅的语言不要,答案语言流畅准确，答案尽量引用查询到结果中键和值。"

    text = get_answer_4(prompt)

    return text


def wenti_youhua_2(LL, v):
    prompt = f"我有一个主线问题为{v}，一步一步的解答结果如下{LL}，请你总结分步解答过程，组织语言完整回答主线问题{v}。\
    【注意】:\
    语言简洁流畅，不要做无关回答和分析。\
    如：经查询，统一社会信用代码是<填充>的公司是<填充>，法人代表是<填充>。"
    # \
    #   总结样例2:经查询，<填充>的公司全称是<填充>，原告是<填充>的案件案号为<填充>，审理法院名称是<填充>

    text = get_answer_4(prompt)

    return text


def sub_answer(ques_zhu, tools):
    # ques_zhu = "(2021)豫0302民初674号的起诉日期是哪个年份，审理日期为，审理法院是？审理法院的地址是？审理法院地址所在区县是？"
    _, api_list_filter, filtered_tools = API_look1.API_look(ques_zhu, tools)
    print(api_list_filter)
    standard_ques = extract_and_parse_json(ques_zhu)
    print("分解后的问题：", standard_ques)
    LL = []
    LL_logger = []
    for k, v in standard_ques.items():
        print(k, v)
        ques = v

        answer, function_result_logger = beijing(ques_zhu, LL, ques, filtered_tools)
        print(answer)
        LL_logger.append(function_result_logger)
        # print(answer)
        d = {k: v, f"{k}查询结果": answer}
        LL.append(d)
    print(LL)
    # print(LL_logger)
    print("------------------回答完成--------------------")
    # print(wenti_youhua(LL_logger,ques_zhu),(LL_logger))
    youhua_text = wenti_youhua_2(LL, ques_zhu)
    # str(wenti_youhua(LL_logger,ques_zhu))+str(LL_logger)
    return youhua_text


def sub_answer_1(ques_zhu):
    API_log = run_v2.API_log
    LL, answer = sub_answer(ques_zhu)
    answer1 = API_diaoyong.API_count_agent(ques_zhu, answer, API_log)
    return answer1


if __name__ == "__main__":
    # API_log=run_v2.API_log
    tools_all = tools.tools_all
    ques_zhu = "查询一下易视腾科技股份有限公司参与的案件有涉案金额的有哪些？涉案金额总和为？"
    """
    answer=sub_answer(ques_zhu)
    answer1=API_diaoyong.API_count_agent(ques_zhu,answer, API_log)

    
   # for i in range(5):
   #     print('-------------输出-------------------')
   #     print(extract_and_parse_json(ques_zhu))

    print(API_log)
    print(answer1)
    """
    print("-----------------------")
    print(sub_answer(ques_zhu, tools_all))
