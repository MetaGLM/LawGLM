from execute_plan import execute_plan
from tool_register.schema import *
from produce_sue import *
from reflexion import *

table_map = {
    "CompanyInfo": CompanyInfoEnum,
    "CompanyRegister": CompanyRegisterEnum,
    "SubCompanyInfo": SubCompanyInfoEnum,
    "LegalDoc": LegalDocEnum,
    "CourtInfo": CourtInfoEnum,
    "CourtCode": CourtCodeEnum,
    "LawfirmInfo": LawfirmInfoEnum,
    "LawfirmLog": LawfirmLogEnum,
    "AddrInfo": AddrInfoEnum,
    "AddrCode": AddrCodeEnum,
    "TempInfo": TempInfoEnum,
    "LegalAbstract": LegalAbstractEnum,
    "XzgxfInfo": XzgxfInfoEnum,
}

log_file = ""

CN_NUM = {
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "零": 0,
    "壹": 1,
    "贰": 2,
    "叁": 3,
    "肆": 4,
    "伍": 5,
    "陆": 6,
    "柒": 7,
    "捌": 8,
    "玖": 9,
    "貮": 2,
    "两": 2,
}

pattern = r"(〇|一|二|三|四|五|六|七|八|九|零|壹|贰|叁|肆|伍|陆|柒|捌|玖|貮|两)(类|次|种|个)"


# log_file = open('log_0804.txt','a')


def replace_match(match):
    number = str(CN_NUM[match.group(1)])  # Get the Arabic number
    word = match.group(2)  # Get the word 类, 次, or 种
    return number + word


def transfer_digit(answer):
    return re.sub(pattern, replace_match, answer)


def is_produce_question(question: str):
    try:
        type_prompt = QUESTION_TYPE.format(action=question)
        type_answer = LLM(type_prompt)
        type = prase_json_from_response(type_answer)["Type"]
    except:
        type = ""
    if type == "民事起诉撰写":
        return 1
    elif type == "整合报告撰写":
        return 2
    else:
        return 0


def run(line):
    re_run = 2  # re_run == 2 代表设置总共可以run2次，可以 重跑 1次
    while re_run > 0:
        question = line["question"]
        needAPI = False
        API_answer = ""
        other_observations = ""
        API_answer_list = []
        question_type = is_produce_question(question)
        answer = ""
        a_answer = ""

        if question_type == 1:
            a_answer = "民事起诉状的答案为：" + process_sue(question)

        elif question_type == 2:
            a_answer = "整合报告的答案为：" + process_report(question)

        question = question.replace("债券", "债权")
        question = question.replace("圈资", "全资")
        question = question.replace("限告", "限高")
        if question.find("区县区划代码") != -1:
            question += "地址是什么？该地址对应的省份城市区县是什么？根据该省份城市区县（在查询时请输入省份、城市、区县字段）查询得到的区县区划代码是多少?"
        if question.find("法院") != -1 and question.find("级别") != -1:
            question += "该法院的行政级别、法院级别和级别分别是什么？"
        if question.find("法院") != -1 and question.find("区县") != -1:
            question += "该法院的法院地址是什么？法院地址所在的区县是哪里？"
        if question.find("城市区划代码") != -1:
            question += "地址是什么？该地址对应的省份城市区县是什么？根据该省份城市区县（在查询时请输入省份、城市、区县字段）查询得到的城市区划代码是多少?"
        if (
                question.find("天气") != -1
                or question.find("最高温度") != -1
                or question.find("最低温度") != -1
                or question.find("湿度") != -1
        ):
            question += (
                "题目中可以查询日期是什么？地址是什么？该地址对应的省份、城市是什么？该省份城市在当天的温度是多少？"
            )

        other_information = ""
        if "起诉时间" in question or "起诉日期" in question:
            other_information = "如果需要筛选，筛选的日期为起诉时间，起诉时间是案号中的括号内年份。"
        if "审理时间" in question or "审理日期" in question:
            other_information = "如果需要筛选，筛选的日期为审理时间，审理时间是字段中的日期信息。"
        if "民事初审" in question:
            other_information += "如果需要筛选，筛选的案件为民事初审案件，案号中需要存在民初"
        if "民事终审" in question:
            other_information += "如果需要筛选，筛选的案件为民事终审案件，案号中需要存在民终"
        if "民事再审" in question:
            other_information += "如果需要筛选，筛选的案件为民事再审案件，案号中需要存在民再"

        for attempt in range(3):
            try:
                query_rewrite_prompt = QUESATION_REWRITE.format(question=question)
                query_rewrite_answer = LLM(query_rewrite_prompt)
                query_rewrite_response = prase_json_from_response(query_rewrite_answer)
                new_question = query_rewrite_response["重写问题"]
                break
            except:
                new_question = question

        if new_question.find("API") != -1 or new_question.find("ＡＰＩ") != -1:
            needAPI = True
        if question.find("API") != -1 or question.find("ＡＰＩ") != -1:
            needAPI = True
        if new_question.find("所聘用的律师事务所") != -1:
            new_question = new_question.replace(
                "所聘用的律师事务所", "作为原告时所聘用的原告律师事务所和作为被告时所有聘用的被告律师事务所"
            )
        if new_question.find("受理费") != -1:
            new_question += "受理费可以查询LegalDoc的判决结果字段获得。"

        new_question += other_information
        code_answer = ""
        try:
            company_code_pattern = r"(\d{5,7})"
            match = re.search(company_code_pattern, new_question)
            des = ""
            if match:
                company_code = match.group(0)
                api_name = "get_company_info"
                args = {"query_conds": {"公司代码": company_code}, "need_fields": []}
                ori_answer = http_api_call(api_name=api_name, data=args)
                if len(ori_answer["输出结果"]) != 0:
                    company_name = ori_answer["输出结果"][0]["公司名称"]
                    des = f" 题目中出现了公司代码{company_code}，经查询，其对应的公司名称为{company_name}"
                    new_question += des  # 添加到new_question中
                    code_answer = f"公司代码{company_code}对应的公司为{company_name}"
        except:
            des = ""
        ### step2: 判断使用哪些表
        for attempt in range(3):
            try:
                table_prompt = TABLE_PROMPT.format(question=new_question, database_schema=database_schema)
                table_answer = LLM(table_prompt)
                table_response = prase_json_from_response(table_answer)
                table = table_response["名称"]
                break
            except:
                table = [
                    "CompanyInfo",
                    "CompanyRegister",
                    "SubCompanyInfo",
                    "LegalDoc",
                    "CourtInfo",
                    "CourtCode",
                    "LawfirmInfo",
                    "LawfirmLog",
                    "AddrInfo",
                    "AddrCode",
                    "TempInfo",
                    "LegalAbstract",
                    "XzgxfInfo",
                ]

        if "CompanyInfo" not in table and des != "":
            table.append("CompanyInfo")

        tool_prompt = ""
        table_used_prompt = ""
        used_tools = []
        for i in table:
            emun = table_map[i]
            one_prompt = f"""
    {i}表格有下列字段：
    {build_enum_list(emun)}
    -------------------------------------
    """
            table_used_prompt += one_prompt + "\n"
            used_tools.extend(Tools_map[i])
            tool_prompt += str(Tools_prompt[i]) + "\n"

        field_response = ""
        for attempt in range(3):
            try:
                Memory_prompt = MEMORY_PROMPT.format(question=question, query_list=query_list)
                Memory_answer = LLM(Memory_prompt)
                Memory_response = prase_json_from_response(Memory_answer)
                Memory_list = Memory_response["相关问题"]
                memory = get_memory(Memory_list)
                break
            except:
                Memory_list = [1, 2, 3, 4, 5]
                memory = get_memory(Memory_list)

        new_question += a_answer
        for attempt in range(3):
            try:
                scratchpad, answer, API_answer, other_observations = execute_plan(
                    new_question,
                    table_used_prompt,
                    used_tools,
                    memory,
                    field_response,
                    log_file,
                    needAPI,
                    API_answer,
                    tool_prompt,
                    API_answer_list,
                    other_information,
                )
                break
            except Exception as e:
                print("运行错误:", question)
                traceback.print_exc()
                answer = question

        if question_type == 0:
            for attempt in range(3):
                try:
                    self_judege_prompt = Self_Judge.format(question=question, answer=answer)
                    self_judege_answer = LLM(self_judege_prompt)
                    self_judege_response = prase_json_from_response(self_judege_answer)
                    break
                except:
                    self_judege_response = {"Answer": "True"}

        old_answer = answer.replace("\n", " ")
        new_answer = ""
        if question_type == 0:
            try:
                if self_judege_response["Answer"] != "True":
                    for attempt in range(3):
                        try:
                            scratchpad, new_answer, other_observations = Reflexion(
                                new_question,
                                table_used_prompt,
                                tool_prompt,
                                old_answer,
                                scratchpad,
                                log_file,
                                used_tools,
                                needAPI,
                                API_answer,
                                API_answer_list,
                                other_information,
                            )
                            new_answer = new_answer.replace("\n", " ")
                            break
                        except Exception as e:
                            traceback.print_exc()
                            new_answer = question
            except:
                self_judege_response = {"Answer": "False"}
                new_answer = question

        # print("old_answer: ", old_answer)
        print("new_answer: ", new_answer)
        answer = simplify_answer(old_answer + new_answer)
        if (
                a_answer != "生成起诉状失败，请检查输入参数是否正确"
                and a_answer != "生成Word文档失败，请检查输入数据是否正确"
        ):
            answer += a_answer
        # if a_answer!= "生成起诉状失败，请检查输入参数是否正确" and a_answer != "生成Word文档失败，请检查输入数据是否正确" and a_answer!="":
        #     answer = a_answer

        answer += code_answer
        answer += other_observations
        answer = remove_commas_from_numbers(answer).replace("℃", "度").replace("摄氏度", "度")
        answer = convert_date_format(answer, 1)
        answer = answer.replace("（", "(").replace("）", ")")
        answer = answer.replace("\n", " ")
        answer = transfer_digit(answer)

        id = line["id"]
        if question_type == 0:
            try:
                if self_judege_response["Answer"] != "True":  # 第一次做不对
                    try:
                        self_judege_prompt = Self_Judge.format(question=question, answer=answer)
                        self_judege_answer = LLM(self_judege_prompt)
                        self_judege_response = prase_json_from_response(self_judege_answer)
                    except:
                        self_judege_response = {"Answer": "False"}
            except:
                self_judege_response = {"Answer": "False"}

            try:
                if self_judege_response["Answer"] != "True":  # 如果第二次做也不对，尝试重跑
                    if re_run > 1:
                        re_run -= 1
                        # print("重跑", re_run)
                        continue  # 不会return，而是进行下一次循环
            except:
                pass
        else:
            id = line["id"]
            save_dict = {}
            save_dict["id"] = int(line["id"])
            save_dict["question"] = line["question"]
            save_dict["answer"] = answer
            return save_dict

        id = line["id"]
        save_dict = {}
        save_dict["id"] = int(line["id"])
        save_dict["question"] = line["question"]
        save_dict["answer"] = answer
        # line['answer'] = answer
        return save_dict


def run_all(line, f):
    a_dict = json.loads(line)
    try:
        answer = run(a_dict)
    except:
        qid = a_dict["id"]
        answer = a_dict["question"]
        traceback.print_exc()

    save_dict = {}
    save_dict["id"] = a_dict["id"]
    save_dict["question"] = a_dict["question"]
    save_dict["answer"] = answer
    f.write(json.dumps(save_dict, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    query_path = "../assets/question_d.json"
    all_querys = [i for i in open(query_path, "r", encoding="utf-8").readlines() if i.strip()][19:20]
    for query in all_querys:
        line = json.loads(query)
        run(line)
