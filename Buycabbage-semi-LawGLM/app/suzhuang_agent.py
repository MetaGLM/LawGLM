from zhipuai import ZhipuAI
import requests
import json
import run_v2

client = ZhipuAI()
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 3BC078EB97F78FB2ABC6B2825A1FE57F783DF2BEE85336CC",  # 团队token:D49……
}


# -------------------------------------------------诉状-------------------------------------------


def generate_lawsuit_dict(
    plaintiff,
    defendant,
    plaintiff_attorney,
    defendant_attorney,
    claim="AA纠纷",
    facts_and_reasons="上诉",
    evidence="PPPPP",
    court_name="最高法",
    filing_date="2012-09-08",
):
    # 参数验证
    if not all([plaintiff, defendant, plaintiff_attorney, defendant_attorney]):
        raise ValueError("原告、被告、原告代理律师、被告代理律师信息必须提供")

    plaintiff_info = run_v2.get_company_info_register("公司名称", plaintiff)
    defendant_info = run_v2.get_company_info_register("公司名称", defendant)

    if not plaintiff_info or not defendant_info:
        raise ValueError("无法获取原告或被告的公司信息")

    plaintiff_attorney_info = run_v2.get_lawfirm_info_log(plaintiff_attorney)
    defendant_attorney_info = run_v2.get_lawfirm_info_log(defendant_attorney)

    if not plaintiff_attorney_info or not defendant_attorney_info:
        raise ValueError("无法获取原告或被告代理律师的信息")

    lawsuit_dict = {
        "原告": plaintiff_info.get("公司名称"),
        "原告地址": plaintiff_info.get("注册地址"),
        "原告法定代表人": plaintiff_info.get("法定代表人"),
        "原告联系方式": plaintiff_info.get("联系电话"),
        "原告委托诉讼代理人": plaintiff_attorney,
        "原告委托诉讼代理人联系方式": plaintiff_attorney_info.get("通讯电话"),
        "被告": defendant_info.get("公司名称"),
        "被告地址": defendant_info.get("注册地址"),
        "被告法定代表人": defendant_info.get("法定代表人"),
        "被告联系方式": defendant_info.get("联系电话"),
        "被告委托诉讼代理人": defendant_attorney,
        "被告委托诉讼代理人联系方式": defendant_attorney_info.get("通讯电话"),
        "诉讼请求": claim,
        "事实和理由": facts_and_reasons,
        "证据": evidence,
        "法院名称": court_name,
        "起诉日期": filing_date,
    }
    return lawsuit_dict


"""

# 定义参数
plaintiff = "深圳市佳士科技股份有限公司"
defendant = "天津凯发电气股份有限公司"
plaintiff_attorney = "山东崇义律师事务所"
defendant_attorney = "山东海金州律师事务所"
claim = "产品生产者责任纠纷"
facts_and_reasons = "因被告生产的产品存在质量问题，导致原告遭受经济损失，经多次协商未果，现提起诉讼。"
evidence = "质量检测报告、经济损失评估报告、往来沟通记录等"
court_name = "辽宁省沈阳市中级人民法院"
filing_date = '2024-04-02'

# 调用函数
lawsuit_info = generate_lawsuit_dict(
    plaintiff=plaintiff,
    defendant=defendant,
    plaintiff_attorney=plaintiff_attorney,
    defendant_attorney=defendant_attorney,
    claim=claim,
    facts_and_reasons=facts_and_reasons,
    evidence=evidence,
    court_name=court_name,
    filing_date=filing_date
)

# 输出或进一步处理生成的诉状信息字典
print(lawsuit_info)






# 定义参数
plaintiff = "河北养元智汇饮品股份有限公司"
defendant = "通威股份有限公司"
plaintiff_attorney = "江苏义科律师事务所"
defendant_attorney = "江苏源实发扬律师事务所"
claim = "买卖合同纠纷"
facts_and_reasons = "被告未能按合同约定交付指定品质及数量的商品，导致原告经济损失，经双方沟通未达成一致解决方案，故提起诉讼。"
evidence = "买卖合同、交货单据、通信记录、损失评估报告等"
court_name = "邯郸市肥乡区人民法院"
filing_date = '2024-01-02'

# 调用函数
lawsuit_info = generate_lawsuit_dict(
    plaintiff=plaintiff,
    defendant=defendant,
    plaintiff_attorney=plaintiff_attorney,
    defendant_attorney=defendant_attorney,
    claim=claim,
    facts_and_reasons=facts_and_reasons,
    evidence=evidence,
    court_name=court_name,
    filing_date=filing_date
)

# 输出或进一步处理生成的诉状信息字典
print(lawsuit_info)
"""


# -----------------------------------------------------整合报告数据报告-------------------------------------------


def filter_cases_by_criteria(cases, year=None, amount_min=None, amount_max=float("inf")):
    """
    筛选案件列表，根据年份和/或金额范围。
    :param cases: 案件列表
    :param year: 筛选的案件发生年度
    :param amount_min: 筛选的案件最低金额（不含），默认为None表示不考虑下限
    :param amount_max: 筛选的案件最高金额（含），默认为正无穷大，表示不考虑上限
    :return: 筛选后的案件列表
    """
    if amount_min is not None and not isinstance(amount_min, (int, float)):
        raise ValueError("最低金额必须是数字或None")
    if not (isinstance(amount_max, (int, float)) or amount_max == float("inf")):
        raise ValueError("最高金额必须是数字或正无穷大")

    filtered_cases = []
    for case in cases:
        if year is not None and case.get("案件发生年度") != str(year):
            continue

        amount = float(case.get("涉案金额", 0))

        if (amount_min is not None and amount <= amount_min) or (amount > amount_max):
            continue

        filtered_cases.append(case)
    return filtered_cases


def filter_cases_by_xzgxf(cases, year=None, amount_min=None, amount_max=float("inf")):
    """
    筛选案件列表，根据年份和/或金额范围。
    :param cases: 案件列表
    :param year: 筛选的案件发生年度
    :param amount_min: 筛选的案件最低金额（不含），默认为None表示不考虑下限
    :param amount_max: 筛选的案件最高金额（含），默认为正无穷大，表示不考虑上限
    :return: 筛选后的案件列表
    """
    #    print(cases)
    ##    print(f"cases 的类型是: {type(cases)}")
    #    if not isinstance(cases, list):
    #      cases = [cases]
    #        print(cases)
    #        print('-----------------------------')
    if amount_min is not None and not isinstance(amount_min, (int, float)):
        raise ValueError("最低金额必须是数字或None")
    if not (isinstance(amount_max, (int, float)) or amount_max == float("inf")):
        raise ValueError("最高金额必须是数字或正无穷大")

    filtered_cases = []
    for case in cases:
        # print(case)
        # print('-----------------------------------')
        # print(case)
        if year is not None and str(year) not in case.get("立案日期"):
            continue

        amount = float(case.get("涉案金额", 0))

        if (amount_min is not None and amount <= amount_min) or (amount > amount_max):
            continue

        filtered_cases.append(case)
    return filtered_cases


# LL=[{'限制高消费企业名称': '玉门拓璞科技开发有限责任公司', '案号': '（2023）甘0981执138号', '法定代表人': '吴俊年', '申请人': '甘肃省敦煌种业集团股份有限公司', '涉案金额': '58226853', '执行法院': '甘肃省酒泉市玉门市人民法院', '立案日期': '2023-01-10 00:00:00', '限高发布日期': '2023-05-25 00:00:00'}, {'限制高消费企业名称': '玉门拓璞科技开发有限责任公司', '案号': '（2022）甘0981执1488号', '法定代表人': '吴俊年', '申请人': '马**', '涉案金额': '4366298', '执行法院': '甘肃省酒泉市玉门市人民法院', '立案日期': '2022-08-01 00:00:00', '限高发布日期': '2022-12-14 00:00:00'}]

# print(filter_cases_by_xzgxf(LL,year=2022))


# 使用方法示例，筛选2019年且涉案金额大于100000的案件
# print(filter_cases_by_criteria(cpwsxx, 2019, amount_min=0))
# print(get_company_info_register('公司名称','甘肃省敦煌种业集团股份有限公司',need_fields=[ "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "经营范围" ]))

import pandas as pd


def generate_company_integrated_report(
    company_name,
    include_business=True,
    include_sub_companies=True,
    include_restrictions=True,
    include_litigations=True,
    year=None,
    amount_min=None,
    amount_max=float("inf"),
    exclude_business_fields=None,
    exclude_litigation_fields=["判决结果"],
    only_wholly_owned: bool = False,
    investment_amount_above: float = 0.0,
):
    def str_to_timestamp(date_str):
        # 尝试将字符串转换为 Timestamp
        timestamp = pd.to_datetime(date_str, errors="coerce")

        # 如果转换成功（即不是 NaT），则返回 Timestamp 对象
        # 否则，返回原字符串
        if pd.notna(timestamp):
            return timestamp
        else:
            return date_str

    def str_to_float_or_original(s):
        try:
            # 尝试将字符串转换为浮点数
            return float(s)
        except ValueError:
            # 如果转换失败（例如，输入不是一个有效的数字字符串），则返回原值
            return s

    exclude_business_fields = run_v2.list_dict(exclude_business_fields) if exclude_business_fields is not None else []
    exclude_litigation_fields = (
        run_v2.list_dict(exclude_litigation_fields) if exclude_litigation_fields is not None else []
    )
    dict_list = {}
    if include_business:
        # gsxx=get_company_info_register('公司名称',company_name,need_fields=[ "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "经营范围"])  #企业简介
        gsxx = run_v2.get_company_register(company_name=company_name, need_fields=[])
        # "企业简介", 是否包含企业简介

        # gsxx_l={'公司名称': gsxx.get('公司名称'),
        #            '登记状态':gsxx.get('登记状态'),
        #           '统一社会信用代码':gsxx.get('统一社会信用代码'),
        #           '参保人数': gsxx.get('参保人数'),
        #            '行业一级': gsxx.get('行业一级'),
        ##            '行业二级':gsxx.get('行业二级'),
        #            '行业三级':gsxx.get('行业三级')}
        gsxx = run_v2.rename_key_in_dict(gsxx, "工商表联系电话", "联系电话")
        gsxx = run_v2.rename_key_in_dict(gsxx, "工商表成立日期", "成立日期")
        gsxx = run_v2.rename_key_in_dict(gsxx, "工商表经营范围", "经营范围")
        # gsxx_l=gsxx
        # if 1: #include_business_not
        #    gsxx_l=[ i for i in gsxx_l if  i not in ['企业简介']]
        if exclude_business_fields:
            exclude_business_fields = ["企业简介" if item == "公司简介" else item for item in exclude_business_fields]
            gsxx_l = {k: v for k, v in gsxx.items() if k not in exclude_business_fields}
        else:
            # 如果没有要排除的字段，则直接使用gsxx的全部内容
            gsxx_l = gsxx.copy()

        gsxx_dict = {"工商信息": [gsxx_l]}
        dict_list["工商信息"] = gsxx_dict["工商信息"]
    # else:
    # dict_list['工商信息']=[{}]
    if include_sub_companies:
        zgsxx = run_v2.get_sub_company_info_list(
            company_name, only_wholly_owned=only_wholly_owned, investment_amount_above=investment_amount_above
        )
        zgs_names = [i["公司名称"] for i in zgsxx]
        zgsxx_dict = {"子公司信息": zgsxx}
        dict_list["子公司信息"] = zgsxx_dict["子公司信息"]

    if include_restrictions:
        # Initialize the list for restrictions
        gxfxx_list = []

        # Get restriction info for the main company
        # gxfxxs_mgs = run_v2.get_xzgxf_info_list(company_name)
        gxfxxs_mgs = run_v2.get_xzgxf_info_list(company_name)
        gxfxx_list.extend(gxfxxs_mgs)
        # print(gxfxx_list)
        # Iterate over subsidiaries to get their restriction info
        for zgs_name in zgs_names:
            # print(zgs_name)
            gxfxxs_zgs = run_v2.get_xzgxf_info_list(zgs_name)
            if not isinstance(gxfxxs_zgs, list):
                gxfxxs_zgs = [gxfxxs_zgs]
                # print(gxfxxs_zgs)
            # print(gxfxxs_zgs)
            gxfxx_list.extend(gxfxxs_zgs)
            # print(gxfxx_list)
        # Filter the gathered records
        print(gxfxx_list)
        gxfxx_list = filter_cases_by_xzgxf(gxfxx_list, year=year, amount_min=amount_min, amount_max=amount_max)

        # Directly assign the filtered list to the dictionary, no need for an intermediate step
        dict_list["限制高消费"] = gxfxx_list

    if include_litigations:
        L_mgs_zgs = []
        cpwsxx_mgs = run_v2.get_legal_document_list(company_name)
        L_mgs_zgs = L_mgs_zgs + cpwsxx_mgs
        for zgs_name in zgs_names:
            cpwszz_zgs = run_v2.get_legal_document_list(zgs_name)
            if not isinstance(cpwszz_zgs, list):
                cpwszz_zgs = [cpwszz_zgs]
            L_mgs_zgs = L_mgs_zgs + cpwszz_zgs
        cpwsxxs = filter_cases_by_criteria(L_mgs_zgs, year=year, amount_min=amount_min, amount_max=amount_max)
        cpwsxx_list = []
        for cpwsxx in cpwsxxs:
            filtered_cpwsxx = {
                k: v
                for k, v in cpwsxx.items()
                if exclude_litigation_fields is None or k not in exclude_litigation_fields
            }
            filtered_cpwsxx = run_v2.rename_key_in_dict(filtered_cpwsxx, "审理日期", "日期")
            filtered_cpwsxx = {k: v for k, v in filtered_cpwsxx.items() if k != "案件发生年度"}
            cpwsxx_list.append(filtered_cpwsxx)
        # cpwsxx_list.append(
        #    {'关联公司':cpwsxx.get('关联公司'),
        #      '原告': cpwsxx.get('原告'),
        #     '被告': cpwsxx.get('被告'),
        #     '案由': cpwsxx.get( '案由'),
        #     '涉案金额':str_to_float_or_original(cpwsxx.get('涉案金额')),
        #     '日期':str_to_timestamp(cpwsxx.get('审理日期'))
        #      })

        cpwsxx_dict = {"裁判文书": cpwsxx_list}
        dict_list["裁判文书"] = cpwsxx_dict["裁判文书"]

    full_report = {"company_name": company_name, "dict_list": str(dict_list)}

    url = f"{domain}/law_api/s1_b/save_dict_list_to_word"
    rsp = requests.post(url, json=full_report, headers=headers)
    # print(rsp.json())
    # print(full_report)
    return rsp.json()


# print(get_xzgxf_info_list('龙建路桥股份有限公司',[]))
# 示例调用
# print(run_v2.get_xzgxf_info_list('滨州西能天然气利用有限公司'))
# report = generate_company_integrated_report('甘肃省敦煌种业集团股份有限公司',year=2019,amount_min=0,exclude_business_fields=["企业简介"],exclude_litigation_fields=['判决结果'])
# print(report)
# %%
# print(run_v2.get_sub_company_info_list('广汇能源股份有限公司'))
"""
#%%
print(generate_company_integrated_report('马应龙药业集团股份有限公司',include_business=True, include_sub_companies=True, 
                                      include_restrictions=True, include_litigations=True, 
                                      year=2020, amount_min=1000000, amount_max=float('inf'),exclude_business_fields=['公司简介'],exclude_litigation_fields=['判决结果']))


#%%
print(generate_company_integrated_report('深圳市瑞丰光电子股份有限公司',include_business=True, include_sub_companies=True, 
                                      include_restrictions=True, include_litigations=True, 
                                      year='2020', amount_min=1000000, amount_max=float('inf'),exclude_business_fields=['公司简介'],exclude_litigation_fields=['判决结果']))

#%%
"""

"""
import pandas as pd
data=json.loads(report['dict_list'].replace("'", "\""))
# 创建DataFrame
business_df = pd.DataFrame(data['工商信息'])
subsidiary_df = pd.DataFrame(data['子公司信息'])
limit_consume_df = pd.DataFrame(data['限制高消费'])
court_doc_df = pd.DataFrame(data['裁判文书'])

# 导出到Excel
with pd.ExcelWriter('甘肃省敦煌种业集团股份有限公司信息.xlsx') as writer:
    business_df.to_excel(writer, sheet_name='工商信息', index=False)
    subsidiary_df.to_excel(writer, sheet_name='子公司信息', index=False)
    limit_consume_df.to_excel(writer, sheet_name='限制高消费', index=False)
    court_doc_df.to_excel(writer, sheet_name='裁判文书', index=False)

print("Excel文件已成功生成！")
#%%
"""
tools_bg_sz = [
    {
        "type": "function",
        "function": {
            "name": "generate_lawsuit_dict",
            "description": "生成一份民生诉讼状，整合原告、被告及其代理律师信息，诉讼请求，事实与理由，诉讼时间，证据及法院信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plaintiff": {"type": "string", "description": "原告的名称，通常是公司或个人全名。"},
                    "defendant": {"type": "string", "description": "被告的名称，通常是公司或个人全名。"},
                    "plaintiff_attorney": {"type": "string", "description": "原告代理律师的姓名。"},
                    "defendant_attorney": {"type": "string", "description": "被告代理律师的姓名。"},
                    "claim": {
                        "type": "string",
                        "description": "诉讼请求的简述，例如'合同违约纠纷'。默认值为'AA纠纷'。",
                        "default": "AA纠纷",
                    },
                    "facts_and_reasons": {
                        "type": "string",
                        "description": "诉讼的事实和理由概述，如'因合同违约提起诉讼'。默认为'上诉'。",
                        "default": "上诉",
                    },
                    "evidence": {
                        "type": "string",
                        "description": "案件关键证据的概括或编号，例如'合同书、邮件往来记录'。默认为'PPPPP'。",
                        "default": "PPPPP",
                    },
                    "court_name": {
                        "type": "string",
                        "description": "受理案件的法院名称，默认为'最高法'。",
                        "default": "最高法",
                    },
                    "filing_date": {
                        "type": "string",
                        "format": "date",
                        "description": "案件的起诉日期，格式YYYY-MM-DD。默认为'2012-09-08'。",
                        "default": "2012-09-08",
                    },
                },
                "required": ["plaintiff", "defendant", "plaintiff_attorney", "defendant_attorney", "court_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_company_integrated_report",
            "description": "生成公司的整合报告，内容可包括工商信息、子公司信息、限制高消费记录及法律诉讼案件等，支持筛选条件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "目标公司的名称。"},
                    "include_business": {
                        "type": "boolean",
                        "description": "是否包含工商信息。只有存在工商字样时才位真，没有工商字样为假",
                    },
                    "include_sub_companies": {
                        "type": "boolean",
                        "description": "是否包含子公司信息。只有存在子公司字样时才位真，没有子公司字样为假",
                    },
                    "include_restrictions": {
                        "type": "boolean",
                        "description": "是否包含限制高消费记录。只有存在限制高消费字样时才位真，没有限制高消费字样为假",
                    },
                    "include_litigations": {
                        "type": "boolean",
                        "description": "是否包含裁判文书信息。只有存在裁判文书字样时才位真，没有裁判文书字样为假",
                    },
                    "year": {"type": "integer", "description": "筛选特定年份的记录，可选。"},
                    "amount_min": {"type": "number", "description": "筛选涉案金额的最小值，可选。"},
                    "amount_max": {"type": "number", "description": "筛选涉案金额的最大值，默认为正无穷大。"},
                    "exclude_business_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
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
                                "企业简介",
                                "经营范围",
                            ],
                            "description": "需要排除的工商信息字段列表，可选。企业简介就代表公司简介，记得转换为企业简介查询",
                        },
                    },
                    "exclude_litigation_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["判决结果"],
                            "default": ["判决结果"],
                            "description": "需要排除的法律诉讼案件信息字段列表，可选。",
                        },
                    },
                },
                "required": [
                    "company_name",
                    "include_business",
                    "include_sub_companies",
                    "include_restrictions",
                    "include_litigations",
                    "year",
                ],
            },
        },
    },
]


# 调用glm4模型
def glm4_create_sz(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-0520",  # 填写需要调用的模型名称
            messages=messages,
            tools=tools_bg_sz,
        )
        print(response)
        print(attempt)
        if "```python" in response.choices[0].message.content:
            # 如果结果包含字符串'python'，则继续下一次循环
            continue
        else:
            # 一旦结果不包含字符串'python'，则停止尝试
            break
    # 检查最终的response是否仍然包含字符串'python'
    # if 'python' in response.choices[0].message.content:
    #  raise ValueError("最终响应中仍然包含字符串'python'")
    # 返回最终的response
    return response


# 执行函数部分
def get_answer_sz(question):
    try:
        function_result_logger = []
        ques = question
        # ques=pre_question.pre_que1(ques)
        messages = []

        messages.append(
            {
                "role": "system",
                "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分",
            }
        )
        messages.append({"role": "user", "content": ques})

        response = glm4_create_sz(15, messages)
        print(response.choices[0].message)
        messages.append(response.choices[0].message.model_dump())
        messages1 = []

        # messages1.append({"role": "system", "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分"})
        messages1.append({"role": "user", "content": ques})

        jisu = 1
        max_iterations = 1  # 设置一个最大循环次数限制
        print("-----------123--------------")

        while response.choices[0].message.tool_calls and jisu <= max_iterations:
            tool_call = response.choices[0].message.tool_calls[0]
            args = tool_call.function.arguments
            print("------------------args-----------------")
            print(args)

            function_result = {}
            """
            function_names = [tool["function"]["name"] for tool in tools]

            # Creating the function_map dictionary
            function_map = {name: name for name in function_names}
                        
            print(function_map)
            """
            function_map = {
                "generate_lawsuit_dict": generate_lawsuit_dict,
                "generate_company_integrated_report": generate_company_integrated_report,
            }

            function_name = tool_call.function.name
            function = function_map.get(function_name)

            if function:
                function_result = function(**json.loads(args))
            # else:
            #    raise ValueError(f"Unknown function: {function_name}")

            print(f"--------第{jisu}次---接口调用查询返回结果---------{function_result}")
            function_result_logger.append(function_result)
            messages1.append({"role": "tool", "content": f"{function_result}", "tool_call_id": tool_call.id})

            print(response.choices[0].message)
            jisu += 1

        if jisu > max_iterations:
            print("达到最大循环次数，退出循环")

        return response.choices[0].message.content, function_result_logger

    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None, None


def merged_dicts(dicts):
    # 初始化一个空字典用于存储合并后的结果
    merged_dict = {}

    # 检查dicts是否是列表类型
    if not isinstance(dicts, list):
        print("传入的参数不是列表类型，无法合并。")
        return merged_dict  # 或者可以选择抛出异常: raise ValueError("参数必须是一个字典列表")

    # 遍历列表中的每个字典，并使用update方法合并
    for d in dicts:
        merged_dict.update(d)

    # 输出合并后的字典
    print(merged_dict)
    return merged_dict


if __name__ == "__main__":
    ques = "大唐华银电力股份有限公司法人与上海现代制药股份有限公司发生了民事纠纷，大唐华银电力股份有限公司委托给了北京国旺律师事务所，上海现代制药股份有限公司委托给了北京浩云律师事务所，请写一份民事起诉状给天津市蓟州区人民法院时间是2024-02-01，注：法人的地址电话可用公司的代替。"

    answer, function_result_logger = get_answer_sz(ques)
    print("----------------------最终模型答案--------------------------")
    # print(answer,function_result_logger)
    print(answer + str(function_result_logger))
