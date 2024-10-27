from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import CompanyInfoEnum, SubCompanyInfoEnum, LegalDocumentEnum, CompanyRegisterEnum


from match_tools.tools_register import register_tool
from apis.api import augment_company_name, http_api_call


@register_tool
def get_sub_company_info(
    sub_company_name: Annotated[str, "子公司名称", True],
) -> SubCompanyInfo:
    """
    根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息。
    可以用来查询母公司相关信息，以及自己作为子公司被投资的信息。
    """
    # company_name = augment_company_name(sub_company_name)
    params = {"query_conds": {"公司名称": sub_company_name}, "need_fields": []}
    api_result = http_api_call("get_sub_company_info", params)

    if type(api_result) == dict and len(api_result["return"]):
        refined_answer = "根据{}查询到:{}".format(sub_company_name, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "无法查询到子公司{}的上市公司投资关联信息。".format(sub_company_name)
        call_api_successfully = False

    tool_result = {
        "condition": sub_company_name,
        "api": "get_sub_company_info",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


@register_tool
def get_sub_company_info_list(
    related_parent_company_name: Annotated[str, "母公司全称", True],
) -> List[SubCompanyInfo]:
    """
    根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list
    """
    params = {
        "query_conds": {
            "关联上市公司全称": related_parent_company_name,
        },
        "need_fields": [],
    }
    api_result = http_api_call("get_sub_company_info_list", params)

    if type(api_result) == dict:
        refined_answer = "查询到母公司{}投资的所有子公司信息:{}".format(
            related_parent_company_name, api_result["return"]
        )
        call_api_successfully = True
    else:
        refined_answer = "无法查询母公司{}投资的子公司信息".format(related_parent_company_name)
        call_api_successfully = False

    tool_result = {
        "condition": related_parent_company_name,
        "api": "get_sub_company_info_list",
        "search_result": api_result["return"],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
