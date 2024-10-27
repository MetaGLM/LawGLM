import requests
from tools_register import register_tool, get_tools, dispatch_tool
from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import CompanyInfoEnum, SubCompanyInfoEnum, LegalDocumentEnum, CompanyRegisterEnum
from config import *

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
    "Authorization": "Bearer 0F7354720533CAACBA57DCA97F89069CB80C78B9BB769786",
}


# Tool Definitions
def http_api_call(api_name, data, max_data_len=None):
    url = f"{domain}/law_api/{api_name}"

    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp

    if max_data_len is None:
        max_data_len = len(final_rsp)
    return {"return_items_count": len(final_rsp), "return": final_rsp[:max_data_len]}


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


@register_tool
def get_company_info(
    company_name: Annotated[list, "公司名称或简称的列表", True],
) -> List[CompanyInfo]:
    """
    根据公司名称获得该公司所有基本信息，可以传入多个公司名称，返回一个列表
    """
    company_name = augment_company_name(company_name)
    return http_api_call("get_company_info", {"company_name": company_name})


@register_tool
def get_company_register(
    company_name: Annotated[list, "公司名称或简称的列表", True],
) -> List[CompanyRegister]:
    """
    根据公司名称获得该公司所有注册信息，可以传入多个公司名称，返回一个列表
    """
    company_name = augment_company_name(company_name)
    return http_api_call("get_company_register", {"company_name": company_name})


@register_tool
def get_sub_company_info(
    company_name: Annotated[list, "母公司名称的列表", True],
) -> SubCompanyInfo:
    """
    根据母公司名称获得该母公司所有的关联投资、母公司等信息，可以传入多个母公司名称，返回一个列表
    """
    company_name = augment_company_name(company_name)
    all_subs = company_name[:]
    for comp_name in company_name:
        # print_log("@@@", http_api_call("search_company_name_by_sub_info", {"key": "关联上市公司全称", "value": comp_name})["return"])
        all_subs += [
            i["公司名称"]
            for i in http_api_call(
                "search_company_name_by_sub_info", {"key": "关联上市公司全称", "value": comp_name}, max_data_len=None
            )["return"]
        ]
        # print_log("!", all_subs)
    print_log(all_subs)
    return http_api_call("get_sub_company_info", {"company_name": all_subs})


@register_tool
def get_sub_company_info_by_sub_comp(
    company_name: Annotated[list, "子公司名称的列表", True],
) -> SubCompanyInfo:
    """
    根据子公司名称获得该子公司所有的关联投资等信息，可以传入多个子公司名称，返回一个列表
    """
    company_name = augment_company_name(company_name)
    return http_api_call("get_sub_company_info", {"company_name": company_name})


@register_tool
def get_legal_document(
    case_num: Annotated[list, "案号", True],
) -> List[LegalDocument]:
    """
    根据案号查询相关法律文书的内容，可以传入多个案号，返回一个列表
    """
    return http_api_call("get_legal_document", {"case_num": case_num})


@register_tool
def search_company_name_by_info(
    key: Annotated[CompanyInfoEnum, "公司基本信息字段名称", True],
    value: Annotated[str, "公司基本信息字段具体的值", True],
) -> str:
    """
    根据公司某个基本信息字段是某个值时，查询所有满足条件的公司名称
    """
    return http_api_call("search_company_name_by_info", {"key": key, "value": value})


@register_tool
def search_company_name_by_register(
    key: Annotated[CompanyRegisterEnum, "公司注册信息字段名称", True],
    value: Annotated[str, "公司注册信息字段具体的值", True],
) -> str:
    """
    根据公司某个注册信息字段是某个值时，查询所有满足条件的公司名称
    """
    return http_api_call("search_company_name_by_register", {"key": key, "value": value})


@register_tool
def search_company_name_by_sub_info(
    key: Annotated[SubCompanyInfoEnum, "子公司融资信息字段名称", True],
    value: Annotated[str, "子公司融资信息信息字段具体的值", True],
) -> str:
    """
    根据子公司融资信息字段是某个值时，查询所有满足条件的子公司名称
    """
    return http_api_call("search_company_name_by_sub_info", {"key": key, "value": value})


@register_tool
def search_case_num_by_legal_document(
    key: Annotated[LegalDocumentEnum, "法律文书信息字段名称", True],
    value: Annotated[str, "法律文书信息字段具体的值", True],
) -> str:
    """
    根据法律文书信息字段是某个值时，查询所有满足条件的法律文书案号
    """
    return http_api_call("search_case_num_by_legal_document", {"key": key, "value": value})


if __name__ == "__main__":
    print_log(get_sub_company_info(**{"company_name": "北京长久物流股份有限公司"}))
