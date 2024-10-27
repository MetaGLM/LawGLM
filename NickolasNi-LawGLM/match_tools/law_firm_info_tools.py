import json
from typing import Annotated, List
from match_tools.schema import LawfirmInfo, LawfirmInfoEnum

from match_tools.tools_register import register_tool
from apis.api import http_api_call
from utils import check_target_property
from match_tools.schema import get_table_property_list


@register_tool
def get_lawfirm_info(
    law_firm_name: Annotated[str, "律师事务所名称", True],
    target_property: Annotated[
        List[LawfirmInfoEnum],
        "律师事务所信息表（名录）的字段列表，比如询问律师事务所的地址信息时，需要填入['律师事务所地址']",
        False,
    ] = None,
) -> LawfirmInfo:
    """
    根据律师事务所名称查询律师事务所名录
    """
    need_fields = target_property if target_property else []
    need_fields = need_fields if check_target_property(get_table_property_list("law_firm_info"), need_fields) else []
    params = {"query_conds": {"律师事务所名称": law_firm_name}, "need_fields": need_fields}
    api_result = http_api_call("get_lawfirm_info", params)

    if type(api_result) == dict:
        refined_answer = "根据律师事务所名称{}查询到:{}".format(law_firm_name, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "查询不到{}的相关信息".format(law_firm_name)
        call_api_successfully = False

    tool_result = {
        "condition": law_firm_name,
        "api": "get_lawfirm_info",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
