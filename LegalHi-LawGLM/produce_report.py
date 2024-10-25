from LLM import LLM
from LLM import LLMs_tools
from prompt import *
from tools_class import *
from tool_register.API import *
import re

import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 5DC959180ACBFF13D363AFFEB38F81CE3AFD8BA74746FBB1",
}

domain = "https://comm.chatglm.cn"

url = f"{domain}/law_api/s1_b/save_dict_list_to_word"

template = {
    "company_name": "北京碧水源科技股份有限公司",
    "dict_list": "{'工商信息': [{'公司名称': '北京碧水源科技股份有限公司', '登记状态': '存续', '统一社会信用代码': '91110000802115985Y', '参保人数': '351', '行业一级': '科学研究和技术服务业', '行业二级': '科技推广和应用服务业', '行业三级': '其他科技推广服务业'}], '子公司信息': [{'关联上市公司全称': '北京碧水源科技股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': 100.0, '上市公司投资金额': '1.06亿', '公司名称': '北京碧海环境科技有限公司'}], '裁判文书': [{'关联公司': '北京碧水源科技股份有限公司', '原告': '四川帝宇水利水电工程有限公司', '被告': '成都碧水源江环保科技有限公司,北京碧水源科技股份有限公司', '案由': '建设程施工合同纠纷', '涉案金额': 0.0, '日期': Timestamp('2019-07-23 00:00:00')}], '限制高消费': [{'限制高消费企业名称': '南京仙林碧水源污水处理有限公司', '案号': '（2024）苏0113执1601号', '申请人': '苏华建设集团有限公司', '涉案金额': '-', '立案日期': Timestamp('2024-04-07 00:00:00'), '限高发布日期': Timestamp('2024-06-24 00:00:00')}]}",
}


def filter_legal_document_list(sub_name, company_name, time, money, mode):
    legal_docs = []
    time_key = "案号" if mode == 1 else "日期"
    for i, sub in enumerate(sub_name):
        sub = sub["公司名称"]
        api_name = "get_legal_document_list"
        try:
            args = {
                "query_conds": {"关联公司": sub},
                "need_fields": [
                    "关联公司",
                    "标题",
                    "案号",
                    "文书类型",
                    "原告",
                    "被告",
                    "原告律师事务所",
                    "被告律师事务所",
                    "案由",
                    "涉案金额",
                    "日期",
                    "文件名",
                ],
            }
            res = API(api_name=api_name, args=args)
            if type(res) == dict:
                r = res
                if r["涉案金额"] != "" and float(r["涉案金额"]) > money * 10000:
                    if r[time_key].find(time) != -1:
                        legal_docs.append(r)
            else:
                for r in res:
                    if r["涉案金额"] != "" and float(r["涉案金额"]) > money * 10000:
                        if r[time_key].find(time) != -1:
                            legal_docs.append(r)
        except:
            pass
    api_name = "get_legal_document_list"
    args = {
        "query_conds": {"关联公司": company_name},
        "need_fields": [
            "关联公司",
            "标题",
            "案号",
            "文书类型",
            "原告",
            "被告",
            "原告律师事务所",
            "被告律师事务所",
            "案由",
            "涉案金额",
            "日期",
            "文件名",
        ],
    }
    res = API(api_name=api_name, args=args)
    if type(res) == dict:
        r = res
        if r["涉案金额"] != "" and float(r["涉案金额"]) > money * 10000:
            if r[time_key].find(time) != -1:
                legal_docs.append(r)
    else:
        for r in res:
            if r["涉案金额"] != "" and float(r["涉案金额"]) > money * 10000:
                if r[time_key].find(time) != -1:
                    legal_docs.append(r)
    return legal_docs


# filter_legal_document_list(sub_name, '利亚德光电股份有限公司')


######################### get_xzgxf_info_list ###############################
def filter_xzgxf_info_list(sub_name, company_name, time, money):
    xzgxf_res = []
    for i, sub in enumerate(sub_name):
        sub = sub["公司名称"]
        api_name = "get_xzgxf_info_list"
        try:
            args = {"query_conds": {"限制高消费企业名称": sub}, "need_fields": []}
            res = API(api_name=api_name, args=args)
            if type(res) == dict:
                r = res
                if r["涉案金额"] != "" and r["涉案金额"] != "-" and float(r["涉案金额"]) > money * 10000:
                    if r["立案日期"].find(time) != -1:
                        xzgxf_res.append(r)
            else:
                for r in res:
                    if r["涉案金额"] != "" and r["涉案金额"] != "-" and float(r["涉案金额"]) > money * 10000:
                        if r["立案日期"].find(time) != -1:
                            xzgxf_res.append(r)
        except:
            break
    api_name = "get_xzgxf_info_list"

    args = {"query_conds": {"限制高消费企业名称": company_name}, "need_fields": []}
    res = API(api_name=api_name, args=args)
    if type(res) == dict:
        r = res
        if r["涉案金额"] != "" and r["涉案金额"] != "-" and float(r["涉案金额"]) > money * 10000:
            if r["立案日期"].find(time) != -1:
                xzgxf_res.append(r)
    else:
        for r in res:
            if r["涉案金额"] != "" and r["涉案金额"] != "-" and float(r["涉案金额"]) > money * 10000:
                if r["立案日期"].find(time) != -1:
                    xzgxf_res.append(r)
    return xzgxf_res


def filter_sub_company_list(sub_name):
    sub_company_list = []
    for i, r in enumerate(sub_name):
        if r["上市公司参股比例"] != "" and float(r["上市公司参股比例"]) == 100:
            value = r["上市公司投资金额"]
            if value == "":
                value = 0
            elif "万" in value:
                value = float(value[:-1])
            elif "亿" in value:
                value = float(value[:-1]) * 10000
            elif len(value) <= 2:
                value = 10000
            else:
                value = float(value)
            if value > 10000:
                sub_company_list.append(r)
    return sub_company_list


def process_report(question):
    register = []
    sub_company_infos = []
    legal_docs = []
    xzgxf_docs = []

    # 提取公司名
    company_name = LLM(f"提取问题中的有限公司名称，问题：{question}，只输出公司名称")
    # 提取时间
    try:
        time = LLM(f"提取问题中的时间，问题：{question}，请自动补齐时间为4位数，如19年补齐为2019年，只输出时间")
        time = re.findall(r"\d+", time)[0]
    except:
        time = "2020"
    # 提取出以 万 为单位的金额
    try:
        money = LLM(f"提取问题中的涉案金额，问题：{question}，单位为万，请直接输出数字")
        money = 0 if question.find("涉案金额不为0") else money
        if money != 0:
            money = float(re.findall(r"\d+", money)[0])
    except:
        money = 10

    need_key = (
        [
            "公司名称",
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "经营范围",
        ]
        if question.find("不包括公司简介") != -1
        else [
            "公司名称",
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "经营范围",
            "企业简介",
        ]
    )

    api_name = "get_company_register"
    args = {"query_conds": {"公司名称": company_name}, "need_fields": need_key}
    res = API(api_name=api_name, args=args)
    register.append(res)

    api_name = "get_sub_company_info_list"
    args = {
        "query_conds": {"关联上市公司全称": company_name},
        "need_fields": ["关联上市公司全称", "上市公司关系", "上市公司参股比例", "上市公司投资金额", "公司名称"],
    }
    res = API(api_name=api_name, args=args)

    sub_company_infos = res

    # 投资过亿 + 全资
    try:
        if question.find("投资金额过亿的全资子公司") != -1:
            sub_company_infos = filter_sub_company_list(sub_company_infos)
    except:
        pass

    try:
        if question.find("立案") != -1:
            # 立案时间，看案号
            # 涉案金额超过 10万
            legal_docs = filter_legal_document_list(sub_company_infos, company_name, time, money, 1)
    except:
        pass

    try:
        if question.find("审理") != -1:
            # 审理时间，看日期
            # 涉案金额超过 10万
            legal_docs = filter_legal_document_list(sub_company_infos, company_name, time, money, 2)
    except:
        pass

    try:
        if question.find("限制高消费") != -1:
            # 立案时间，看日期，涉案金额，超过10万
            xzgxf_docs = filter_xzgxf_info_list(sub_company_infos, company_name, time, money)
    except:
        pass

    args = {"company_name": "", "dict_list": "{'工商信息': [], '子公司信息': [], '裁判文书': [], '限制高消费': []}"}

    dict_list = {}
    dict_list["工商信息"] = register
    dict_list["子公司信息"] = sub_company_infos
    dict_list["裁判文书"] = legal_docs
    dict_list["限制高消费"] = xzgxf_docs

    args["dict_list"] = json.dumps(dict_list, ensure_ascii=False)
    rsp = requests.post(url, json=args, headers=headers)
    return rsp.text


def process_report2(question):
    print(question)

    q1, q2 = question.split("，")

    # stage 1: 查询符合要求的子公司
    response = LLM(PRODUCE_WORD_PROMPT[1].format(question=q1))
    plan = prase_json_from_response(response)
    print("一阶段计划为：", plan)

    information = []  # 公司工商信息、子公司信息
    company_name = []  # 所有公司名称列表
    ori_answer = ""  # 原始结果
    for subplan in plan:
        former = subplan["是否需要前序结果"]
        q = subplan["问题"]
        if former == "True":
            q = str(ori_answer) + q
        if subplan["操作"] == "筛选":
            for i in range(3):
                input = q
                prompt = filter_prompt.format(input=input)
                print(prompt)
                ori_answer = prase_json_from_response(LLM(prompt))
                print("the final res is ", ori_answer)
                q = str(ori_answer) + subplan["问题"]
        else:
            query = get_tool_prompt.format(question=q)
            used_tools = [register_tool_one(get_company_register)]
            used_tools.append(register_tool_one(get_sub_company_info_list))
            api_name, api_args = LLMs_tools(query, used_tools)
            ori_answer = http_api_call(api_name=api_name, data=api_args)
            information.append(ori_answer)
    information[-1] = ori_answer
    sub_name = ""
    if len(ori_answer) != 0:
        sub_name = str(ori_answer)
    prompt = extract_company_name.format(info=q1 + sub_name)
    print(prompt)
    ori_answer = prase_json_from_response(LLM(prompt))
    print(ori_answer)

    print("二阶段........")
    # stage 2: 查询符合要求的裁判文书
    response = LLM(PRODUCE_WORD_PROMPT[2].format(question=q2[:-5]))
    plan = prase_json_from_response(response)
    print("二阶段计划为：", plan)

    for subplan in plan:
        subplan["问题"] = str(ori_answer) + subplan["问题"]
        print("\n\n\n" + subplan["问题"])
        if subplan["操作"] == "筛选":
            prompt = filter_legalDoc_prompt.format(question=subplan["问题"])
            ori_answer = prase_json_from_response(LLM(prompt))
            print("符合条件的裁判文书为: ", ori_answer)
            information.append(ori_answer)
        else:
            query = get_tool_prompt_legalDoc.format(question=subplan["问题"])
            ori_answer = []
            used_tools = [register_tool_one(get_legal_document_list)]
            api_name, api_args = LLMs_tools(query, used_tools)
            for k in api_args:
                if k == "query_conds":
                    if type(api_args[k]["关联公司"]) != str:
                        if type(api_args[k]["关联公司"]) == dict:
                            for name in api_args[k]["关联公司"]["Items"]:
                                new_args = api_args
                                new_args["query_conds"]["关联公司"] = name
                                legal_doc = http_api_call(api_name=api_name, data=new_args)
                                if len(legal_doc) != 0:
                                    ori_answer.append(http_api_call(api_name=api_name, data=new_args))
                        elif type(api_args[k]["关联公司"]) == list:
                            for name in api_args[k]["关联公司"]:
                                new_args = api_args
                                new_args["query_conds"]["关联公司"] = name
                                legal_doc = http_api_call(api_name=api_name, data=new_args)
                                if len(legal_doc) != 0:
                                    ori_answer.append(legal_doc)
                    else:
                        legal_doc = http_api_call(api_name=api_name, data=args)
                        if len(legal_doc) != 0:
                            ori_answer.append(legal_doc)

    # 4. 处理信息
    print("\n\n\n", information)

    prompt = deal_information.format(information=information, question=question, template=template)
    args = prase_json_from_response(LLM(prompt))
    print("\n\n\n", args)

    # 5. 生成得到文书

    rsp = requests.post(url, json=args, headers=headers)
    return rsp.text
