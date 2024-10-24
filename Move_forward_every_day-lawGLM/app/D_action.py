import re
from collections import Counter
from copy import deepcopy

from D_LLM import LLM
from D_tools import TOOLS
from D_prompt import (
    API_MAP,
    API_TOOL_MAP,
    TEST_RETRIEVE_PROMPT2,
    PREVIOUS_TASK_PROMPT,
    ORDER_PROMPT,
    INDEX_PROMPT,
    STAT_ANALYSIS_PROMPT,
    MULTI_RETRIEVE_PROMPT,
    PRE_FILTER_LIST_PROMPT,
    FILTER_LIST_PROMPT,
    PROMPT_USER_SUE_USER,
)


from new_logtool import VLOG


class Action:
    # 公司名称检查
    @staticmethod
    def get_company_name_info(company_name, context_data={}):
        full_name, simple_name, code_name = [], [], []

        company_list = [company_name]
        if "省" in company_name or "市" in company_name or "区" in company_name:
            new_company_name = company_name.replace("省", "").replace("市", "").replace("区", "")
            company_list.append(new_company_name)

        company_list2 = deepcopy(company_list)
        for name in company_list:
            pattern = re.compile(r"([\u4e00-\u9fa5])\1+")
            name2 = pattern.sub(r"\1", name)
            if name2 not in company_list2:
                company_list2.append(name2)
            pattern2 = re.compile(r"([\u4e00-\u9fa5])\1")
            name3 = pattern2.sub(r"\1", name)
            if name3 not in company_list2:
                company_list2.append(name3)

        company_list2 = list(set(company_list2))
        full_name = company_list2

        for company in company_list2:
            if len(company) <= 5:
                simple_name.append(company)
            if len(company.strip("公司")) <= 5:
                simple_name.append(company.strip("公司"))
            if len(company.strip("有限公司")) <= 5:
                simple_name.append(company.strip("有限公司"))
        simple_name = list(set(simple_name))

        number_search = re.search(r"\d+", company_name)
        if number_search:
            numbers = number_search.group()
            if len(numbers) >= 6:
                code_name.append(numbers)
            pattern = re.compile(r"(\d)\1+")
            numbers2 = pattern.sub(r"\1", numbers)
            if len(numbers2) >= 6 and numbers2 != numbers:
                code_name.append(numbers2)
            pattern3 = re.compile(r"(\d)\1")
            numbers3 = pattern3.sub(r"\1", numbers)
            if len(numbers3) >= 6 and numbers3 != numbers:
                code_name.append(numbers3)
        code_name = list(set(code_name))

        VLOG[2]("COMPANY_NAME_LIST:", full_name, simple_name, code_name)

        company_result = []
        try:
            for name in full_name:
                if "get_company_info" + "|" + name in context_data:
                    res = context_data["get_company_info" + "|公司名称|" + name]
                else:
                    res = TOOLS.api(api_name="get_company_info", args={"key": "公司名称", "value": name})
                if res:
                    context_data["get_company_info" + "|公司名称|" + name] = res
                    if res not in company_result:
                        company_result.append(res)
            for name in simple_name:
                if "get_company_info" + "|公司简称|" + name in context_data:
                    res = context_data["get_company_info" + "|公司简称|" + name]
                else:
                    res = TOOLS.api(api_name="get_company_info", args={"key": "公司简称", "value": name})
                if res:
                    context_data["get_company_info" + "|公司简称|" + name] = res
                    if res not in company_result:
                        company_result.append(res)
            for name in code_name:
                if "get_company_info" + "|公司代码|" + name in context_data:
                    res = context_data["get_company_info" + "|公司代码|" + name]
                else:
                    res = TOOLS.api(api_name="get_company_info", args={"key": "公司代码", "value": name})
                if res:
                    context_data["get_company_info" + "|公司代码|" + name] = res
                    if res not in company_result:
                        company_result.append(res)
        except Exception as e:
            VLOG[2]("ERROR_CHECK_COMPANY_API:", e)

        return full_name, company_result, context_data

    def retrieve(
        task_index,
        big_question,
        sub_task,
        previous_task="",
        previous_answer="",
        previous_data=[],
        history_info=[],
        context_data={},
        solution="",
        api="",
    ):
        context_data["重要信息"] = []
        api_info = API_MAP.get(api, "")
        api_tool = API_TOOL_MAP.get(api, "")

        api_info_key = re.search(r"\[.*?\]", api_info)
        if api_info_key:
            api_info_key = api_info_key.group()[1:-1]
        else:
            api_info_key = ""

        if task_index == 1:
            previous_task_info = ""
            context_data_str = ""
        else:
            if len(str(previous_data)) > 3000:
                previous_data = str(previous_data)[0:3000]
            else:
                previous_data = str(previous_data)
            # if len(str(context_data)) > 3000:
            #     context_data_str = str(context_data)[0:3000]
            # else:
            #     context_data_str = str(context_data)
            if api == "API16":
                complex_data = context_data["history_data"]
                VLOG[2]("COMPLEX_DATA:", complex_data)
            else:
                complex_data = ""

            previous_task_info = PREVIOUS_TASK_PROMPT.format(
                previous_task=previous_task,
                previous_answer=previous_answer,
                previous_data=previous_data,
                history_info=history_info,
                complex_data=complex_data,
            )

        prompt = TEST_RETRIEVE_PROMPT2.format(
            big_question=big_question,
            sub_task=sub_task,
            previous_task_info=previous_task_info,
            solution=solution,
            api_info=api_info,
            api_info_key=api_info_key,
        )

        VLOG[2]("RETRIVE_PROMPT:", prompt)
        response = TOOLS.prase_json_from_response(LLM.get_llm(prompt, do_sample=False))

        VLOG[2]("RETRIVE:", response)

        task_data = []
        api_data = []
        api_data_list = []
        new_task_question = sub_task

        assist_info = ""

        key = api_info_key
        if key in ("省份+城市+日期", "省份+城市+区县"):
            if isinstance(response, list):
                response = "".join(response)
            else:
                response = str(response)
        for value in TOOLS.wrapper_list_text(response):
            if not value:
                continue

            # 公司分支
            if "公司名称" in key or "公司简称" in key or "公司代码" in key:
                response_company_list = TOOLS.wrapper_list_text(value)

                for company_name in response_company_list:
                    VLOG[2]("ORIGINAL_COMPANY_NAME:", company_name)

                    # 上市公司名称校正
                    full_name, company_result, context_data = Action.get_company_name_info(company_name, context_data)

                    if len(company_result) > 0:
                        assist_info += (
                            "\n已知问题的主体信息为公司名称（全称）：" + company_result[0]["公司名称"] + "。"
                        )
                        assist_info += "\n据查询，" + company_result[0]["公司名称"] + " 是上市公司。"
                        important_info = value + "公司全称为：" + company_result[0]["公司名称"]
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)
                    else:
                        assist_info += f"\n据查询，{company_name} 不是上市公司。"

                    new_company_name = list(set([company["公司名称"] for company in company_result]))

                    VLOG[2]("NEW_COMPANY_NAME:", new_company_name)

                    company_register_info = []
                    for name in set(new_company_name + full_name):
                        if "get_company_register" + "|" + name in context_data:
                            res = context_data["get_company_register" + "|" + name]
                        else:
                            res = TOOLS.api(api_name="get_company_register", args={"company_name": name})

                        if res:
                            context_data["get_company_register" + "|" + name] = res
                            if res not in company_register_info:
                                company_register_info.append(res)
                    if len(company_result) == 0 and len(company_register_info) > 0:
                        new_company_name = list(set([company["公司名称"] for company in company_register_info]))
                        assist_info += "\n已知问题的主体信息为公司名称（全称）：" + ",".join(new_company_name)

                    short_name = full_name[0]
                    for name in full_name:
                        if len(name) < len(short_name):
                            short_name = name

                    all_name = new_company_name + [short_name]

                    for company in company_result:
                        if "经营范围" not in big_question:
                            company["经营范围"] = ""
                        if "简介" not in big_question:
                            company["机构简介"] = ""
                    for company in company_register_info:
                        if "经营范围" not in big_question:
                            company["经营范围"] = ""
                        if "简介" not in big_question:
                            company["企业简介"] = ""

                    if len(company_result) > 0:
                        task_data.extend(company_result)
                        if context_data["is_sue"]:
                            if "原告" in sub_task:
                                context_data["company_info2"].extend(company_result)
                            if "被告" in sub_task:
                                context_data["company_info4"].extend(company_result)
                    if len(company_register_info) > 0:
                        task_data.extend(company_register_info)
                        if context_data["is_sue"]:
                            if "原告" in sub_task:
                                context_data["company_info1"].extend(company_register_info)
                            if "被告" in sub_task:
                                context_data["company_info3"].extend(company_register_info)

                    new_task_question = sub_task + assist_info

                    if api_tool == "get_company_info":
                        api_data = company_result
                    elif api_tool == "get_company_register":
                        api_data = company_register_info
                    elif api_tool in (
                        "get_legal_document_list",
                        "get_sub_company_info",
                        "get_sub_company_info_list",
                        "get_xzgxf_info_list",
                    ):
                        api_args = {"company_name": all_name[0]}
                        if api_tool + "|" + api_args["company_name"] in context_data:
                            res = context_data[api_tool + "|" + api_args["company_name"]]
                        else:
                            res = TOOLS.api(api_name=api_tool, args=api_args)
                        if res:
                            if api_tool == "get_legal_document_list":
                                for case in res:
                                    case["审理日期"] = case["日期"]
                            res = context_data[api_tool + "|" + api_args["company_name"]] = res
                            api_data = TOOLS.wrapper_list(res)
                            task_data.extend(api_data)

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append(api_tool)
                        api_data_list.extend(api_data)

            elif "法院代字" in key and "法院" not in str(value):
                response_courtcode_list = TOOLS.wrapper_list_text(value)
                response_courtcode_list = [TOOLS.transfer_courtcode(x) for x in response_courtcode_list]

                for courtcode in response_courtcode_list:
                    courtcode_info = []
                    if "get_court_code" + "|" + courtcode in context_data:
                        res = context_data["get_court_code" + "|" + courtcode]
                    else:
                        res = TOOLS.api(api_name="get_court_code", args={"court_code": courtcode})
                    if res:
                        context_data["get_court_code" + "|" + courtcode] = res
                        courtcode_info.append(res)
                        api_data = courtcode_info
                        task_data.extend(courtcode_info)
                        assist_info += f"\n已知问题的主体信息为法院代字：{courtcode}。"

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append("get_court_code")
                        api_data_list.extend(api_data)

            elif "法院名称" in key:
                response_court_list = TOOLS.wrapper_list_text(value)

                for court_name in response_court_list:
                    # 法院名称校正
                    court_name = TOOLS.fix_court_name(court_name)
                    VLOG[2]("new_court_name:", court_name)

                    court_info = []
                    if "get_court_info" + "|" + court_name in context_data:
                        res = context_data["get_court_info" + "|" + court_name]
                    else:
                        res = TOOLS.api(api_name="get_court_info", args={"court_name": court_name})
                    if res:
                        context_data["get_court_info" + "|" + court_name] = res
                        court_info.append(res)
                        task_data.extend(court_info)

                    court_code_info = []
                    if "get_court_code" + "|" + court_name in context_data:
                        res2 = context_data["get_court_code" + "|" + court_name]
                    else:
                        res2 = TOOLS.api(api_name="get_court_code", args={"court_name": court_name})
                    if res2:
                        context_data["get_court_code" + "|" + court_name] = res2
                        court_code_info.append(res2)
                        task_data.extend(court_code_info)

                    if res or res2:
                        assist_info += f"\n已知问题的主体信息为法院名称：{court_name}。"
                        important_info = "正确法院名称为：" + court_name
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)

                    if api_tool == "get_court_info":
                        api_data = court_info
                    elif api_tool == "get_court_code":
                        api_data = court_code_info

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append(api_tool)
                        api_data_list.extend(api_data)

            elif "法院代字" in key:
                response_courtcode_list = TOOLS.wrapper_list_text(value)
                response_courtcode_list = [TOOLS.transfer_courtcode(x) for x in response_courtcode_list]

                for courtcode in response_courtcode_list:
                    courtcode_info = []
                    if "get_court_code" + "|" + courtcode in context_data:
                        res = context_data["get_court_code" + "|" + courtcode]
                    else:
                        res = TOOLS.api(api_name="get_court_code", args={"court_code": courtcode})
                    if res:
                        context_data["get_court_code" + "|" + courtcode] = res
                        courtcode_info.append(res)
                        api_data = courtcode_info
                        task_data.extend(courtcode_info)

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append("get_court_code")
                        api_data_list.extend(api_data)

            elif key == "案号":
                response_case_id_list = TOOLS.wrapper_list_text(value)
                response_case_id_list1 = list(set([LLM.get_case_id(x) for x in response_case_id_list if x]))
                response_case_id_list2 = [LLM.get_case_id2(x) for x in response_case_id_list1]
                response_case_id_list_final = list(
                    set(response_case_id_list + response_case_id_list1 + response_case_id_list2)
                )
                for case_id in response_case_id_list_final:
                    case_info = []
                    if "get_legal_document" + "|" + case_id in context_data:
                        res = context_data["get_legal_document" + "|" + case_id]
                    else:
                        res = TOOLS.api(api_name="get_legal_document", args={"case_id": case_id})
                    if res:
                        try:
                            res["审理日期"] = res["日期"]
                        except:
                            pass
                        context_data["get_legal_document" + "|" + case_id] = res
                        case_info.append(res)
                        task_data.extend(case_info)

                    case_abstract = []
                    if "get_legal_abstract" + "|" + case_id in context_data:
                        res2 = context_data["get_legal_abstract" + "|" + case_id]
                    else:
                        res2 = TOOLS.api(api_name="get_legal_abstract", args={"case_id": case_id})
                    if res2:
                        context_data["get_legal_abstract" + "|" + case_id] = res2
                        case_abstract.append(res2)
                        task_data.extend(case_abstract)

                    res3 = ""
                    if "执" in case_id:
                        case_xzgxf = []
                        if "get_xzgxf_info" + "|" + case_id in context_data:
                            res3 = context_data["get_xzgxf_info" + "|" + case_id]
                        else:
                            res3 = TOOLS.api(api_name="get_xzgxf_info", args={"case_id": case_id})
                        if res3:
                            context_data["get_xzgxf_info" + "|" + case_id] = res3
                            case_xzgxf.append(res3)
                            task_data.extend(case_xzgxf)

                    case_courtname = []
                    if "get_court_name" + "|" + case_id in context_data:
                        res4 = context_data["get_court_name" + "|" + case_id]
                    else:
                        res4 = TOOLS.api(api_name="get_court_name", args={"case_id": case_id})
                    if res4:
                        context_data["get_court_name" + "|" + case_id] = res4
                        case_courtname.append(res4)
                        task_data.extend(case_courtname)

                    if res or res2 or res3:
                        assist_info += f"\n已知正确的案号为：{case_id}。"
                        important_info = "正确的案号为：" + case_id
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)

                    if api_tool == "get_legal_document":
                        api_data = case_info
                    elif api_tool == "get_legal_abstract":
                        api_data = case_abstract
                    elif api_tool == "get_xzgxf_info":
                        api_data = case_xzgxf
                    elif api_tool == "get_court_name":
                        api_data = case_courtname

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append(api_tool)
                        api_data_list.extend(api_data)

            elif key == "律师事务所名称":
                response_lawfirm_list = TOOLS.wrapper_list_text(value)
                for lawfirm in response_lawfirm_list:
                    lawfirm_info = []
                    if "get_lawfirm_info" + "|" + lawfirm in context_data:
                        res = context_data["get_lawfirm_info" + "|" + lawfirm]
                    else:
                        res = TOOLS.api(api_name="get_lawfirm_info", args={"lawfirm_name": lawfirm})
                    if res:
                        context_data["get_lawfirm_info" + "|" + lawfirm] = res
                        lawfirm_info.append(res)
                        task_data.extend(lawfirm_info)

                        if context_data["is_sue"]:
                            if "原告" in sub_task:
                                context_data["lawfirm_info1"].extend(lawfirm_info)
                            if "被告" in sub_task:
                                context_data["lawfirm_info2"].extend(lawfirm_info)

                    lawfirm_log = []
                    if "get_lawfirm_log" + "|" + lawfirm in context_data:
                        res2 = context_data["get_lawfirm_log" + "|" + lawfirm]
                    else:
                        res2 = TOOLS.api(api_name="get_lawfirm_log", args={"lawfirm_name": lawfirm})
                    if res2:
                        context_data["get_lawfirm_log" + "|" + lawfirm] = res2
                        lawfirm_log.append(res2)
                        task_data.extend(lawfirm_log)

                    if res or res2:
                        assist_info += f"\n已知问题的主体信息为律师事务所名称：{lawfirm}。"
                        important_info = "律师事务所名称为：" + lawfirm
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)

                    if api_tool == "get_lawfirm_info":
                        api_data = lawfirm_info
                    elif api_tool == "get_lawfirm_log":
                        api_data = lawfirm_log

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append(api_tool)
                        api_data_list.extend(api_data)

            elif key == "统一社会信用代码":
                response_code_list = TOOLS.wrapper_list_text(value)

                for code in response_code_list:
                    code_info = []
                    if "get_company_register_name" + "|" + code in context_data:
                        res = context_data["get_company_register_name" + "|" + code]
                    else:
                        res = TOOLS.api(api_name="get_company_register_name", args={"统一社会信用代码": code})
                    if res:
                        context_data["get_company_register_name" + "|" + code] = res
                        code_info.append(res)
                        api_data = code_info
                        task_data.extend(code_info)
                        assist_info += f"\n已知问题的主体信息为公司的统一社会信用代码：{code}。"
                        important_info = "该公司统一社会信用代码为：" + code
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append("get_company_register_name")
                        api_data_list.extend(api_data)

            elif key == "地址":
                response_address_list = TOOLS.wrapper_list_text(value)
                for address in response_address_list:
                    address_info = []
                    if "get_address_info" + "|" + address in context_data:
                        res = context_data["get_address_info" + "|" + address]
                    else:
                        res = TOOLS.api(api_name="get_address_info", args={"地址": address})
                    if res:
                        context_data["get_address_info" + "|" + address] = res
                        address_info.append(res)
                        api_data = address_info
                        task_data.extend(address_info)
                        assist_info += f"\n已知问题的主体信息为地址：{address}。"
                        important_info = "地址为：" + address
                        if important_info not in context_data["重要信息"]:
                            context_data["重要信息"].append(important_info)

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append("get_address_info")
                        api_data_list.extend(api_data)

            else:
                for xvalue in TOOLS.wrapper_list_text(value):
                    if key == "省份+城市+日期":
                        tools = TOOLS.get_api_tools(["API6_3"])
                        assist_info = f"\n已知问题的主体信息为地址和日期为：{xvalue}。"
                    elif key == "省份+城市+区县":
                        tools = TOOLS.get_api_tools(["API6_2"])
                        assist_info = f"\n已知问题的主体信息为省份城市区县为：{xvalue}。"

                    else:
                        tools = TOOLS.get_api_tools(["API6_2", "API6_3"])
                        assist_info = f"\n已知问题的主体信息为 {key}, {xvalue}。"

                    VLOG[2]("API_TOOLS:", tools)

                    new_task_question = sub_task + assist_info

                    api_name, api_args = TOOLS.get_tools_response(new_task_question, tools)
                    VLOG[2]("API_INFO:", api_name, api_args)
                    # 地理位置修正
                    api_args = TOOLS.fix_address(api_args)

                    if "date" in api_args:
                        if "x" in api_args["date"] or "X" in api_args["date"]:
                            prompt = """请根据上下文信息，给出日期信息，包含详细的年、月、日。上下文信息：{new_task_question}。\n前面累计的信息：{history_info}。\
                                直接回复日期即可，不要回复其它内容。""".format(
                                new_task_question=new_task_question, history_info=history_info
                            )
                            response = LLM.get_llm(prompt)
                            api_args["date"] = response
                            VLOG[2]("NEW_DATE:", api_args["date"])
                        try:
                            api_args["date"] = TOOLS.transfer_date(api_args["date"])
                        except:
                            pass

                    if api_name is None:
                        VLOG[2]("WRANING_NO_API_NAME:", new_task_question, tools)
                    else:
                        if api_name + "|" + str(api_args) in context_data:
                            res = context_data[api_name + "|" + str(api_args)]
                        else:
                            res = TOOLS.api(api_name=api_name, args=api_args)
                        if res:
                            context_data[api_name + "|" + str(api_args)] = res
                            api_data = TOOLS.wrapper_list(res)
                            task_data.extend(api_data)

                    if len(api_data) > 0 and len(api_data[0]) > 0:
                        context_data["api_count"] += 1
                        context_data["api_type"].append(api_name)
                        api_data_list.extend(api_data)

        # if len(task_data) == 0:
        #     task_data = previous_data

        if len(api_data_list) == 0:
            api_data_list = previous_data

        new_task_question = sub_task + assist_info

        if api == "API4":
            task_answer = f"根据统计，该公司查询到的案件列表有：{len(api_data_list)}个。"
            if len(context_data["重要信息"]) > 0:
                task_answer += "此步骤重要信息：" + ",".join(context_data["重要信息"])
        elif api == "API6":
            task_answer = f"根据统计，该公司查询到的子公司数量有：{len(api_data_list)}个。"
            if len(context_data["重要信息"]) > 0:
                task_answer += "此步骤重要信息：" + ",".join(context_data["重要信息"])
        elif api == "API7":
            task_answer = f"根据统计，该公司查询到限制高消费相关案件有：{len(api_data_list)}个。"
            if len(context_data["重要信息"]) > 0:
                task_answer += "此步骤重要信息：" + ",".join(context_data["重要信息"])
        elif len(task_data) == 0:
            task_answer = "此步骤未查询到信息。"
            if len(context_data["重要信息"]) > 0:
                task_answer += "此步骤重要信息：" + ",".join(context_data["重要信息"])
        else:
            task_answer = LLM.answer_simple(
                new_task_question, task_data, history_info=history_info, important_info=context_data["重要信息"]
            )
            if len(context_data["重要信息"]) > 0:
                task_answer += "此步骤重要信息：" + ",".join(context_data["重要信息"])
        context_data["important"].append(str(context_data["重要信息"]))
        return new_task_question, task_answer, api_data_list, task_data, context_data

    def stat_num(question, api_data_list=[]):
        if not api_data_list or not isinstance(api_data_list, list):
            task_answer = "据统计，上一个步骤给出的数据列表总数是0个。"
        else:
            task_answer = f"据统计，上一个步骤给出的数据列表总数是{len(api_data_list)}个。"

        return task_answer

    def stat_sum(question, api_data_list=[]):
        prompt = f"""
问题：{question}

判断该问题是否需要对某类属性进行求和，如果需要，请给出属性名称。以下是部分示例：
问题：给定案件列表，求涉案总金额
回答：涉案金额

问题：给定公司列表，对投资金额进行统计/求和
回答：投资金额

问题：给定案件列表，查询案号信息
回答：不是求和问题

请直接输出属性名称，不回答问题，不输出其他信息。
""".strip()

        response = LLM.get_llm(prompt)

        assist_info = ""
        if "涉案金额" in response:
            cash_list = [TOOLS.transfer_cash(str(x.get("涉案金额", 0))) for x in api_data_list]
            cash_sum = sum(cash_list)
            assist_info = f"涉案总金额为{cash_sum}元"

        if "投资金额" in response:
            cash_list = [TOOLS.transfer_cash(str(x.get("上市公司投资金额", 0))) for x in api_data_list]
            cash_sum = sum(cash_list)
            assist_info = f"投资总金额为{cash_sum}元"

        if not assist_info:
            assist_info = str(api_data_list)
        task_answer = LLM.refine_answer_simple(question, assist_info)
        return task_answer

    def caseid_parse(big_question, question, previous_answer="", api_data_list=[]):
        court_code_list = []

        result = TOOLS.caseid_search(question)
        if not result:
            result = TOOLS.caseid_search(previous_answer)
        if not result and len(api_data_list) > 0:
            for data in api_data_list:
                case_id = data.get("案号", "")
                if case_id:
                    court_code = TOOLS.transfer_courtcode(case_id)
                    if court_code != case_id:
                        court_code_list.append(court_code)

        if not court_code_list:
            result = TOOLS.caseid_search(big_question)

        for x in result:
            court_code = TOOLS.transfer_courtcode(x)
            if court_code != x:
                court_code_list.append(court_code)

        court_code_list = list(set(court_code_list))
        task_answer = f"根据案号信息，查询到的法院代字是：{court_code_list}"
        return task_answer

    def order(question, api_data_list=[], context_data={}):
        if len(api_data_list) == 0:
            task_answer = "此步骤没有数据可排序。"
            return task_answer, api_data_list

        prompt = ORDER_PROMPT.format(question=question)

        import heapq

        def top_k_elements_with_indices(lst, k, reverse=False):
            indexed_lst = [(val, idx) for idx, val in enumerate(lst)]
            if not reverse:
                top_k = heapq.nlargest(k, indexed_lst)
            else:
                top_k = heapq.nsmallest(k, indexed_lst)
            top_k_values, top_k_indices = zip(*top_k)
            return list(top_k_indices), list(top_k_values)

        response = LLM.get_llm(prompt, model="glm-4-air", do_sample=False)
        feature = TOOLS.prase_json_from_response(response)
        VLOG[2]("FEATURE:", feature)

        sort_feature = feature["排序属性"]
        if "投资金额" in sort_feature:
            sort_feature = "上市公司投资金额"
        elif "涉案金额" in sort_feature:
            sort_feature = "涉案金额"
        elif "法院级别" in sort_feature:
            sort_feature = "法院级别"
            api_data_list = Action.get_court_level(api_data_list)

        sort_type = False
        if "排序方式" in feature and "升序" in feature["排序方式"]:
            sort_type = True

        sort_num = len(api_data_list)

        value_list = []
        for xdata in api_data_list:
            if not isinstance(xdata, dict):
                continue
            value = TOOLS.transfer_cash(str(xdata.get(sort_feature, 0)))
            value_list.append(value)

        idx, _ = top_k_elements_with_indices(value_list, sort_num, sort_type)

        # target_value = [api_data_list[i].get(sort_feature, "0") for i in result_idx]

        task_data = [api_data_list[i] for i in idx]
        VLOG[2]("TEST")
        VLOG[2](context_data["current_task_index"])

        task_info_key = "task_" + str(context_data["current_task_index"])
        VLOG[2]("TASK_INFO_KEY:", task_info_key)

        context_data[task_info_key] = [sort_feature, sort_type]
        VLOG[2]("TEST2")

        assist_info = f"排序属性为{sort_feature}，排序方式为{'升序' if sort_type else '降序'}。"
        # task_answer = LLM.refine_answer_simple(question, assist_info)

        # VLOG[2]("SORT:", task_answer)
        return assist_info, task_data

    def index(question, history_info=[], api_data_list=[], context_data={}):
        if len(api_data_list) == 0:
            task_answer = "没有找到符合条件的数据。"
            return task_answer, api_data_list

        previous_info = history_info[-1]

        prompt = INDEX_PROMPT.format(question=question, previous_info=previous_info)
        VLOG[2]("INDEX_PROMPT:", prompt)
        response = LLM.get_llm(prompt, model="glm-4-air", do_sample=False)
        response = TOOLS.prase_json_from_response(response)
        VLOG[2]("INDEX:", response)

        index = response["索引值"]

        task_data = []
        for i in index:
            if i < len(api_data_list):
                task_data.append(api_data_list[i])

        feature = context_data["task_" + str(context_data["current_task_index"] - 1)][0]
        feature_list = [x.get(feature, "0") for x in task_data]

        assist_info = f"找到符合条件的结果：{task_data}, 对应的{feature}为{feature_list}"
        # task_answer = LLM.refine_answer_simple(question, assist_info)
        return assist_info, task_data

    def stat_analysis(question, history_info=[], api_data_list=[]):
        if len(api_data_list) == 0:
            task_answer = "此步骤没有数据可分析。"
            return task_answer, api_data_list

        prompt = STAT_ANALYSIS_PROMPT.format(question=question, history_info=history_info)
        response = LLM.get_llm(prompt, model="glm-4-air", do_sample=False)
        response = TOOLS.prase_json_from_response(response)
        VLOG[2]("STAT_ANALYSIS:", response)

        stat_list = []

        original_feature = response["统计属性"]
        feature = response["统计属性"]
        if "年份" in feature or "时间" in feature:
            feature = "案号"

        for xdata in api_data_list:
            if feature == "案号":
                year = re.findall(r"20\d{2}", xdata.get("案号", ""))
                if year:
                    stat_list.append(year[0])
            else:
                if feature in xdata:
                    stat_list.append(xdata.get(feature, "0"))

        if len(stat_list) == 0:
            return "没有找到符合条件的数据。", api_data_list
        result = Counter(stat_list)
        most_common = result.most_common(1)[0][0]
        common_value = result[most_common]

        task_answer = f"根据统计，{original_feature}中出现次数最多的是{most_common}，共出现{common_value}次。"
        return task_answer, api_data_list

    def summary(question, history_info=[], api_data_list=[]):
        task_answer = LLM.refine_answer_info(question, api_data_list, history_info)
        return task_answer

    def get_court_level(api_data_list):
        if (
            len(api_data_list) == 0
            or not isinstance(api_data_list, list)
            or not isinstance(api_data_list[0], dict)
            or "案号" not in api_data_list[0]
        ):
            return api_data_list

        for data in api_data_list:
            case_id = data.get("案号", "")
            if case_id:
                court_code = TOOLS.transfer_courtcode(case_id)
                data["法院代字"] = court_code
            res = TOOLS.api(api_name="get_court_code", args={"court_code": court_code})
            if res:
                data["法院级别"] = res.get("法院级别", 0)

        return api_data_list

    def multi_retrieve(question, api_key, api_data_list=[]):
        if not api_data_list:
            task_answer = "没有信息可查询"
            return task_answer, api_data_list
        try:
            keys = list(api_data_list[0].keys())
            VLOG[2]("MULTI_RETRIEVE_KEYS:", keys)
        except Exception as e:
            VLOG[2]("ERROR_MULTI_RETRIEVE:", e)
            return "没有信息可查询", api_data_list

        if len(api_data_list) > 50:
            task_answer = "列表数量为{}个。".format(len(api_data_list))
            return task_answer, api_data_list

        api_info = API_MAP.get(api_key, "")

        prompt = MULTI_RETRIEVE_PROMPT.format(api_info=api_info, keys=keys)

        VLOG[2]("MULTI_RETRIEVE_PROMPT:", prompt)

        response = LLM.get_llm(prompt)
        VLOG[2]("MULTI_RETRIEVE:", response)
        feature = TOOLS.prase_json_from_response(response)["查询选项"]

        api_name = API_TOOL_MAP.get(api_key, "")

        task_answer_list = []
        datalist = []

        prompt2 = """
        请完成下面的任务：{question}
        已知在这个列表中，某个元素是 {target}
        相关api信息如下：
        {api_response}
        请根据问题和信息，简要回答，务必保持简洁。
        """.strip()
        for xdata in api_data_list:
            if feature not in xdata:
                continue

            api_args = {}
            if api_key in ("API2", "API3", "API4", "API5", "API6", "API7"):
                api_args = {"company_name": xdata[feature]}
            elif api_key in ("API8", "API9", "API18"):
                api_args = {"case_id": xdata[feature]}
            elif api_key in ("API10", "API11"):
                api_args = {"court_name": xdata[feature]}
            elif api_key in ("API12", "API13"):
                api_args = {"lawfirm_name": xdata[feature]}

            api_response = TOOLS.api(api_name=api_name, args=api_args)
            if api_response:
                datalist.append(api_response)

            prompt = prompt2.format(question=question, target=xdata[feature], api_response=api_response)

            response = LLM.get_llm(prompt, model="glm-4-air", do_sample=False)
            task_answer_list.append(response)

        task_answer = str(task_answer_list)
        if not datalist:
            datalist = api_data_list

        return task_answer, datalist

    def filter_list(question, history_info=[], api_data_list=[]):
        if not isinstance(api_data_list, list) or not api_data_list:
            return LLM.refine_answer_simple(question, api_data_list), api_data_list

        simple_filter_prompt = PRE_FILTER_LIST_PROMPT.format(question=question)
        simple_response = LLM.get_llm(simple_filter_prompt)

        VLOG[2]("FILTER_LIST_SIMPLE:", simple_response)

        task_data = []
        for xdata in api_data_list:
            if "选项8" in simple_response:
                prompt = FILTER_LIST_PROMPT.format(question=question, xdata=xdata)
                response = LLM.get_llm(prompt, model="glm-4-air", do_sample=False)
                if "yes" in response and "no" not in response:
                    task_data.append(xdata)
                # filter_key = simple_response.split(",")[-1]
                # if filter_key in str(xdata):
                #     task_data.append(xdata)
            elif "选项1" in simple_response:
                year1 = re.findall(r"\d{4}", question)
                year2 = re.findall(r"\d{4}", simple_response)
                target_year = year2[0] if year2 else year1[0]
                if isinstance(xdata, dict):
                    if target_year in xdata.get("案号", ""):
                        task_data.append(xdata)
                elif isinstance(xdata, str):
                    if target_year in xdata:
                        task_data.append(xdata)
            elif "选项2" in simple_response:
                year1 = re.findall(r"\d{4}", question)
                year2 = re.findall(r"\d{4}", simple_response)
                target_year = year2[0] if year2 else year1[0]
                if isinstance(xdata, dict):
                    if target_year in xdata.get("日期", ""):
                        task_data.append(xdata)
                elif isinstance(xdata, str):
                    if target_year in xdata:
                        task_data.append(xdata)
            elif "选项3" in simple_response:
                threshold = TOOLS.transfer_cash(simple_response.split("于")[-1])
                if "大于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("涉案金额", "0")) > threshold:
                        task_data.append(xdata)
                elif "小于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("涉案金额", "0")) < threshold:
                        task_data.append(xdata)
                elif "不等于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("涉案金额", "0")) != threshold:
                        task_data.append(xdata)
                elif "等于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("涉案金额", "0")) == threshold:
                        task_data.append(xdata)
            elif "选项4" in simple_response:
                target_type = simple_response.split(",")[-1]
                target_name = ""
                if "被告" in target_type or "被起诉人" in target_type:
                    target_name = xdata.get("被告", "")
                elif "原告" in target_type or "起诉人" in target_type:
                    target_name = xdata.get("原告", "")

                for name in target_name.split(","):
                    if name.strip() and name.strip() in question + str(history_info):
                        task_data.append(xdata)
                        break
            elif "选项5" in simple_response:
                if isinstance(xdata, dict):
                    rate = TOOLS.transfor_rate(xdata.get("上市公司参股比例", "0"))
                    if rate == 100:
                        task_data.append(xdata)
            elif "选项6" in simple_response:
                threshold = TOOLS.transfer_cash(simple_response.split("于")[-1])
                if "大于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("上市公司投资金额", "0")) > threshold:
                        task_data.append(xdata)
                elif "小于" in simple_response:
                    if isinstance(xdata, dict) and TOOLS.transfer_cash(xdata.get("上市公司投资金额", "0")) < threshold:
                        task_data.append(xdata)
                elif "不等于" in simple_response:
                    if (
                        isinstance(xdata, dict)
                        and TOOLS.transfer_cash(xdata.get("上市公司投资金额", "0")) != threshold
                    ):
                        task_data.append(xdata)
                elif "等于" in simple_response:
                    if (
                        isinstance(xdata, dict)
                        and TOOLS.transfer_cash(xdata.get("上市公司投资金额", "0")) == threshold
                    ):
                        task_data.append(xdata)
            elif "选项7" in simple_response:
                court_name = simple_response.split(",")[-1]
                court_name = TOOLS.fix_court_name(court_name)
                res = TOOLS.api(api_name="get_court_code", args={"court_name": court_name})
                if res:
                    court_code = res.get("法院代字", court_name)
                    if xdata.get("案号", "") and court_code in xdata.get("案号", ""):
                        task_data.append(xdata)

        raw_answer = f"原有列表数量：{len(api_data_list)}条，筛选后的列表数量：{len(task_data)}条。"
        VLOG[2]("FILTER_LIST:", raw_answer)
        return raw_answer, task_data

    @staticmethod
    def get_sue_task(question=""):
        task_list = [
            {
                "子任务": "已知：{question}。根据问题描述，分辨出原告公司和被告公司是谁？只需要回答原告与被告，务必保持简洁，不要写起诉状。".format(
                    question=question
                ),
                "操作": "总结",
            },
            {
                "子任务": "根据原告公司名称查询其工商注册信息，返回原告公司名称、法定代表人、联系方式等信息",
                "操作": "API3",
            },
            {
                "子任务": "根据被告公司名称查询工商注册信息，返回公司名称、法定代表人、联系方式、地址等信息",
                "操作": "API3",
            },
            {
                "子任务": "已知：{question}。根据问题描述，分辨出原告委托代理人（律师事务所）和被告委托代理人（律师事务所）是？".format(
                    question=question
                ),
                "操作": "总结",
            },
            {"子任务": "根据原告律师事务所名称，查询负责人、联系方式等信息。", "操作": "API12"},
            {"子任务": "根据被告律师事务所名称，查询负责人、联系方式等信息。", "操作": "API12"},
            {
                "子任务": "根据原告和被告公司名称、工商注册信息、上市公司信息，原告和被告委托代理人（律师事务所）信息，填写诉讼信息表格，并生成诉讼信息",
                "操作": "诉讼",
            },
        ]
        return task_list

    @staticmethod
    def get_sue_info(question, context_data={}):
        prompt = PROMPT_USER_SUE_USER.format(
            sue_info=question,
            company_info1=context_data["company_info1"],
            company_info2=context_data["company_info2"],
            company_info3=context_data["company_info3"],
            company_info4=context_data["company_info4"],
            lawfirm_info1=context_data["lawfirm_info1"],
            lawfirm_info2=context_data["lawfirm_info2"],
        )

        VLOG[2]("SUE_PROMPT:", prompt)

        response = LLM.get_llm(prompt, do_sample=False)
        VLOG[2]("SUE_RESPONSE:", response)
        req_dict = TOOLS.prase_json_from_response(response)
        VLOG[2]("SUE_REQ_DICT:", req_dict)

        sue_key = [
            "原告",
            "原告地址",
            "原告法定代表人",
            "原告联系方式",
            "原告委托诉讼代理人",
            "原告委托诉讼代理人联系方式",
            "被告",
            "被告地址",
            "被告法定代表人",
            "被告联系方式",
            "被告委托诉讼代理人",
            "被告委托诉讼代理人联系方式",
            "诉讼请求",
            "事实和理由",
            "证据",
            "法院名称",
            "起诉日期",
        ]

        sue_dict = {}
        for key in sue_key:
            if key not in req_dict:
                sue_dict[key] = ""
            else:
                sue_dict[key] = req_dict[key]

        result = TOOLS.sue_api(api_name="get_company_sue_company", args=sue_dict)
        VLOG[2]("SUE_RESULT:", result)
        return result
