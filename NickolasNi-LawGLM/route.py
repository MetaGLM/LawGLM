from model import call_glm
from prompts import TABLE_PROMPT, QUESTION_CLASS, TABLE_PROMPT_SEPARATE


def predict_direct_or_tools(query, use_LLM=True):
    if use_LLM:
        messages = [{"role": "user", "content": QUESTION_CLASS.format(query=query)}]
        response = call_glm(messages)
        classified_result = response.choices[0].message.content

        if classified_result.__contains__("3"):
            return "其他查询问题"
        elif classified_result.__contains__("2"):
            return "整合报告"
        else:
            return "诉讼书"
    else:
        if query.__contains__("起诉状") or query.__contains__("写一份"):
            return "诉讼书"
        elif query.__contains__("整合报告"):
            return "整合报告"
        else:
            return "其他查询问题"


def get_related_tables(query):
    messages = [
        # {"role": "user", "content": TABLE_PROMPT.format(question=query)}
        {"role": "user", "content": TABLE_PROMPT_SEPARATE.format(question=query)}
    ]
    response = call_glm(messages)
    return response.choices[0].message.content


table_2_tools = {
    "company_info": ["get_company_info", "get_company_register_name"],
    "company_register": ["get_company_register", "get_company_register_name"],
    "sub_company_info": ["get_sub_company_info", "get_sub_company_info_list"],
    "legal_doc": ["get_legal_document", "get_legal_document_list"],
    "court_info": ["get_court_info"],
    "court_code": ["get_court_code"],
    "law_firm_info": ["get_lawfirm_info"],
    "law_firm_log": ["get_lawfirm_log"],
    "addr_info": ["get_address_info"],
    "addr_code": ["get_address_code"],
    "temp_info": ["get_temp_info"],
    "legal_abstract": ["get_legal_abstract"],
    "xzgxf_info": ["get_xzgxf_info_list", "get_xzgxf_info"],
}


web_search_tool = {"type": "web_search", "web_search": {"enable": False}}


def enhance_tables(tables, query):
    if "company_info" not in tables:
        tables.append("company_info")
    if "company_register" not in tables:
        tables.append("company_register")
    # if query["question"].__contains__('公司'):
    #     if 'company_info' not in tables:
    #         tables.append('company_info')
    #     if 'company_register' not in tables:
    #         tables.append('company_register')
    if (
        query["question"].__contains__("涉案")
        or query["question"].__contains__("案号")
        or query["question"].__contains__("审理")
    ):
        if "legal_doc" not in tables:
            tables.append("legal_doc")
    if (
        query["question"].__contains__("地址")
        or query["question"].__contains__("城市")
        or query["question"].__contains__("省")
        or query["question"].__contains__("区县")
    ):
        if "addr_info" not in tables:
            tables.append("addr_info")
        if "addr_code" not in tables:
            tables.append("addr_code")
    if query["question"].__contains__("法院"):
        if "court_info" not in tables:
            tables.append("court_info")
        if "court_code" not in tables:
            tables.append("court_code")
    if query["question"].__contains__("事务所") or query["question"].__contains__("律所"):
        if "law_firm_info" not in tables:
            tables.append("law_firm_info")
        if "law_firm_log" not in tables:
            tables.append("law_firm_log")
    if "court_info" in tables and "court_code" not in tables:
        tables.append("court_code")
    if "court_info" not in tables and "court_code" in tables:
        tables.append("court_info")
    if "law_firm_info" in tables and "law_firm_log" not in tables:
        tables.append("law_firm_log")
    if "law_firm_info" not in tables and "law_firm_log" in tables:
        tables.append("law_firm_info")


def route_tools(tables, tools):
    tool_keys = []
    for table in tables:
        tool_keys.extend(table_2_tools[table])
    tool_keys = list(set(tool_keys))
    routed_tools = []
    for tool_key in tool_keys:
        routed_tools.append(tools[tool_key])
    routed_tools.append(web_search_tool)
    return routed_tools


def get_tools_sue(tools):
    routed_tools = []
    routed_tools.append(web_search_tool)
    routed_tools.append(tools["get_company_info"])
    routed_tools.append(tools["get_sue"])
    return routed_tools
