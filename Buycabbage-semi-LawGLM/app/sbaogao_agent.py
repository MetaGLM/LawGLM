from zhipuai import ZhipuAI

import pandas as pd
import requests
import json

import run_v2

client = ZhipuAI()
domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 3BC078EB97F78FB2ABC6B2825A1FE57F783DF2BEE85336CC",  # 团队token:D49……
}


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
        print("-----------------include_business----------------------")
        # gsxx=get_company_info_register('公司名称',company_name,need_fields=[ "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "经营范围"])  #企业简介
        gsxx = run_v2.get_company_register(company_name=company_name, need_fields=[])

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
            # 检查是否已经是列表，如果不是，则包装成列表
        if not isinstance(gsxx_l, list):
            gsxx_l = [gsxx_l]
        gsxx_dict = {"工商信息": gsxx_l}
        dict_list["工商信息"] = gsxx_dict["工商信息"]
    # else:
    # dict_list['工商信息']=[{}]
    if include_sub_companies:
        print("------------------include_sub_companies----------------------")
        zgsxx = run_v2.get_sub_company_info_list(
            company_name, only_wholly_owned=only_wholly_owned, investment_amount_above=investment_amount_above
        )
        zgs_names = [i["公司名称"] for i in zgsxx]
        zgsxx_dict = {"子公司信息": zgsxx}
        dict_list["子公司信息"] = zgsxx_dict["子公司信息"]
    if include_restrictions:
        print("-----------------include_restrictions-----------------------")
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
        # print(gxfxx_list)
        gxfxx_list = filter_cases_by_xzgxf(gxfxx_list, year=year, amount_min=amount_min, amount_max=amount_max)

        # Directly assign the filtered list to the dictionary, no need for an intermediate step
        dict_list["限制高消费"] = gxfxx_list

    if include_litigations:
        print("-----------------include_litigations-----------------------")
        L_mgs_zgs = []
        cpwsxx_mgs = run_v2.get_legal_document_list(company_name)
        L_mgs_zgs = L_mgs_zgs + cpwsxx_mgs
        for zgs_name in zgs_names:
            print(f"-----------------for  {zgs_names} in zgs_names:-----------------------")
            cpwszz_zgs = run_v2.get_legal_document_list(zgs_name)
            if not isinstance(cpwszz_zgs, list):
                cpwszz_zgs = [cpwszz_zgs]
            L_mgs_zgs = L_mgs_zgs + cpwszz_zgs
        cpwsxxs = filter_cases_by_criteria(L_mgs_zgs, year=year, amount_min=amount_min, amount_max=amount_max)
        cpwsxx_list = []
        for cpwsxx in cpwsxxs:
            print("-----------------for cpwsxx in cpwsxxs:-----------------------")
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

    full_report = {"company_name": company_name, "dict_list": dict_list}

    return full_report


# run_v2.get_company_register('龙建路桥股份有限公司')

# full_report=generate_company_integrated_report(**{"amount_min":0,"company_name":"甘肃省敦煌种业集团股份有限公司","exclude_litigation_fields":{"Items":["判决结果"]},"include_business":True,"include_litigations":True,"include_restrictions":True,"include_sub_companies":True,"year":2019})
# full_report=generate_company_integrated_report(**{"amount_min":0,"company_name":"龙建路桥股份有限公司","exclude_business_fields":["企业简介"],"exclude_litigation_fields":["判决结果"],"investment_amount_above":100000000,"only_wholly_owned":True,"year":2019})

# print(generate_company_integrated_report(**{"amount_min":1,"company_name":"龙建路桥股份有限公司","exclude_business_fields":["企业简介"],"exclude_litigation_fields":["判决结果"],"investment_amount_above":100000000,"only_wholly_owned":True,"year":2019}))

tools_bg_sz = [
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
                        "description": "是否需要工商信息。只有存在工商字样时才位真，没有工商字样为假",
                    },
                    "include_sub_companies": {
                        "type": "boolean",
                        "description": "是否需要子公司信息。只有存在子公司字样时才位真，没有子公司字样为假",
                    },
                    "include_restrictions": {
                        "type": "boolean",
                        "description": "是否需要限制高消费记录。只有存在限制高消费字样时才位真，没有限制高消费字样为假",
                    },
                    "include_litigations": {
                        "type": "boolean",
                        "description": "是否需要裁判文书信息。只有存在裁判文书字样时才位真，没有裁判文书字样为假",
                    },
                    "year": {"type": "integer", "description": "筛选特定年份的记录，可选。"},
                    "amount_min": {"type": "number", "description": "筛选涉案金额的最小值，可选。"},
                    "amount_max": {"type": "number", "description": "筛选涉案金额的最大值，默认为正无穷大。"},
                    "exclude_business_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
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
                            "enum": [
                                "关联公司",
                                "原告",
                                "被告",
                                "原告律师事务所",
                                "被告律师事务所",
                                "案由",
                                "涉案金额",
                                "判决结果",
                                "日期",
                                "文件名",
                                "标题",
                                "文书类型",
                            ],
                            "default": ["判决结果"],
                            "description": "需要排除的法律诉讼案件信息字段列表，可选。",
                        },
                    },
                    "only_wholly_owned": {"type": "boolean", "description": "是否需要全资子公司"},
                    "investment_amount_above": {
                        "type": "number",
                        "description": "子公司投资金额超过多少钱，投资金额过亿，值为100000000.00",
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
    }
]
## TODO： 这里有问题
def glm4_create_bg(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=messages,
            tools=tools_bg_sz,
        )
        print("------------------------调用了 glm4_create_bg------------------")
        if "```python" in response.choices[0].message.content:
            continue
        else:
            break
    return response


# 执行函数部分
def get_answer_bg(question):
    try:
        ques = question
        messages = []

        messages.append(
            {
                "role": "system",
                "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分",
            }
        )
        messages.append({"role": "user", "content": ques})

        response = glm4_create_bg(2, messages)
        messages.append(response.choices[0].message.model_dump())
        messages1 = []
        messages1.append({"role": "user", "content": ques})

        jisu = 1
        max_iterations = 1
        print("-----------123--------------")

        if response.choices[0].message.tool_calls and jisu <= max_iterations:
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
            function_map = {"generate_company_integrated_report": generate_company_integrated_report}

            function_name = tool_call.function.name
            function = function_map.get(function_name)

            if function:
                function_result = function(**json.loads(args))

        return response.choices[0].message.content, function_result

    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")

        return None, None
def transform_string(s):
    # Split the string by underscores
    parts = s.split("_")
    companyregister_index = None
    for i, part in enumerate(parts):
        if part.startswith("companyregister"):
            companyregister_index = i
            break

    # If found, replace 'companyregister1_18' with 'companyregister0_0' and remove the next part (the number 18)
    if companyregister_index is not None and companyregister_index + 1 < len(parts):
        parts[companyregister_index] = "companyregister0_0"
        del parts[companyregister_index + 1]  # Remove the number 18

    # Join the parts back together
    return "_".join(parts)


def bg_yz_1(ques):
    _, full_report = get_answer_bg(ques)
    # print(full_report)
    dict_list_1 = full_report["dict_list"]

    full_report_new = {"company_name": full_report["company_name"], "dict_list": str(dict_list_1)}

    url = f"{domain}/law_api/s1_b/save_dict_list_to_word"
    rsp = requests.post(url, json=full_report_new, headers=headers)
    # print(full_report_new)
    print(rsp.json())
    s_string = rsp.json()

    if "工商" not in ques:
        s_string = transform_string(s_string)

    return s_string


def bg_yz(ques):
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts:
        try:
            result = bg_yz_1(ques)
            print(f"尝试 {attempt + 1} 的结果: {result}")
            if ("失败" not in result):
                print("成功生成 word！")
                return result
            attempt += 1
        except Exception as e:
            print(f"发生异常: {e}")
            attempt += 1
    print("达到最大尝试次数，未成功生成 word。")
    return result


if __name__ == "__main__":
    ques1 = "甘肃省敦煌种业集团股份有限公司关于工商信息（不需要经验范围和公司简介）及子公司信息，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果,也不需要文件名）整合报告。"
    print(bg_yz(ques1))
