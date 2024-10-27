from typing import Annotated, List
from match_tools.schema import XzgxfInfo

from match_tools.tools_register import register_tool
from apis.api import augment_company_name, http_api_call


@register_tool
def get_xzgxf_info(
    case_num: Annotated[
        str,
        "法律裁判文书的案号。案号通常由年份、法院代字和案件序号三部分组成，如：(2020)赣0781民初1260号、(2019)川01民终12104号，年份用括号()包裹",
        True,
    ],
) -> XzgxfInfo:
    """
    根据法律裁判文书的案号查询限制高消费相关信息
    """
    case_num = case_num.replace("(", "（").replace(")", "）")
    params = {
        "query_conds": {
            "案号": case_num,
        },
        "need_fields": [],
    }
    api_result = http_api_call("get_xzgxf_info", params)
    if len(api_result["return"]) == 0:
        case_num = case_num.replace("（", "(").replace("）", ")")
        params = {
            "query_conds": {
                "案号": case_num,
            },
            "need_fields": [],
        }
        api_result = http_api_call("get_xzgxf_info", params)

    if type(api_result) == dict and len(api_result["return"]):
        refined_answer = "根据{}查询到:{}".format(case_num, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "无法根据{}查询到限制高消费相关信息。".format(case_num)
        call_api_successfully = False

    tool_result = {
        "condition": case_num,
        "api": "get_xzgxf_info",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


@register_tool
def get_xzgxf_info_list(
    company_name: Annotated[str, "限制高消费企业名称", True],
    # target_property: Annotated[List[LegalDocumentEnum], "查询关联公司法律文书的目标字段，比如询问'关于某公司起诉日期在2020年且作为被起诉人的涉案总金额为多少时'需要填入['被告','涉案金额','日期']", False]
    # target_property: Annotated[List[LegalDocumentEnum], "法律文书的字段列表，如果问题对于法律文书的某些字段进行限制或者查询则填写这些字段，比如询问'关于某公司起诉日期在2020年且作为被起诉人的涉案总金额为多少时'需要填入['被告','涉案金额','日期']", False]
) -> List[XzgxfInfo]:
    """
    根据企业名称查询所有限制高消费相关信息list
    """
    params = {
        "query_conds": {
            "限制高消费企业名称": company_name,
        },
        "need_fields": [],
    }
    api_result = http_api_call("get_xzgxf_info_list", params)

    if type(api_result) == dict:
        refined_answer = "查询到与{}相关联的限制高消费信息:{}".format(company_name, api_result["return"])
        call_api_successfully = True
    else:
        refined_answer = "无法查询到与{}相关联的限制高消费信息".format(company_name)
        call_api_successfully = False

    tool_result = {
        "condition": company_name,
        "api": "get_xzgxf_info_list",
        "search_result": api_result["return"],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
