from typing import Annotated, List
from match_tools.schema import LawfirmLog, LawfirmLogEnum

from match_tools.tools_register import register_tool
from match_tools.schema import get_table_property_list
from utils import parse_json_from_response, check_target_property
from apis.api import http_api_call


@register_tool
def get_lawfirm_log(
    law_firm_name: Annotated[str, "律师事务所名称", True],
    target_property: Annotated[
        List[LawfirmLogEnum],
        "律师事务所业务数据表的字段列表，比如询问某律所服务已上市公司的数量时，需要填入['服务已上市公司']",
        False,
    ] = None,
) -> LawfirmLog:
    """
    根据律师事务所名称查询律师事务所统计数据
    """
    need_fields = target_property if target_property else []
    need_fields = need_fields if check_target_property(get_table_property_list("law_firm_log"), need_fields) else []
    params = {"query_conds": {"律师事务所名称": law_firm_name}, "need_fields": need_fields}
    api_result = http_api_call("get_lawfirm_log", params)

    if type(api_result) == dict:
        refined_answer = "律师事务所名称{}查询到:{}".format(law_firm_name, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "查询名为{}的律师事务所业务数据信息".format(law_firm_name)
        call_api_successfully = False

    tool_result = {
        "condition": law_firm_name,
        "api": "get_lawfirm_log",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
