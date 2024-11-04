import requests
from match_tools.tools_register import register_tool, get_tools, dispatch_tool
from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import CompanyInfoEnum, SubCompanyInfoEnum, LegalDocumentEnum, CompanyRegisterEnum

api_list = [
    "get_company_info",
    "search_company_name_by_info",
    "get_company_register",
    "search_company_name_by_register",
    "get_sub_company_info",
    "search_company_name_by_sub_info",
    "get_legal_document",
    "search_case_num_by_legal_document",
]

domain = "https://comm.chatglm.cn"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",
}


# Tool Definitions
def http_api_call(api_name, data, max_data_len=None):
    url = f"{domain}/law_api/s1_b/{api_name}"
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()

    if isinstance(final_rsp, float):
        return final_rsp
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp

    if max_data_len is None:
        max_data_len = len(final_rsp)
    return {"return_items_count": len(final_rsp), "return": final_rsp[:max_data_len]}


def http_api_call_original(api_name, data):
    url = f"{domain}/law_api/s1_b/{api_name}"
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    return final_rsp

def get_company_name_by_bref(bref):
    company_names = [
        i["公司名称"]
        for i in http_api_call("search_company_name_by_info", {"key": "公司简称", "value": bref})["return"]
    ]
    return company_names


def get_company_name_by_en(bref):
    company_names = [
        i["公司名称"]
        for i in http_api_call("search_company_name_by_info", {"key": "英文名称", "value": bref})["return"]
    ]
    return company_names


def augment_company_name(company_name):
    company_name = company_name if isinstance(company_name, list) else [company_name]
    for c in company_name[:]:
        company_name += get_company_name_by_bref(c)
        company_name += get_company_name_by_en(c)
        company_name += [c.replace("(", "（").replace(")", "）")]
        company_name += [c.replace("（", "(").replace("）", ")")]

    return list(set(company_name))
