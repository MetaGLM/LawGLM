from typing import Annotated, List
from match_tools.schema import CourtCode, CourtCodeEnum

from match_tools.tools_register import register_tool
from match_tools.schema import get_table_property_list
from utils import parse_json_from_response, check_target_property
from apis.api import http_api_call


@register_tool
def get_court_code(
    court_name: Annotated[str, "法院名称", False] = None,
    court_code: Annotated[str, "法院代字", False] = None,
    target_property: Annotated[
        List[CourtCodeEnum],
        "法院地址信息、代字表的字段列表，比如已知法院代字询问法院名时，需要填入['法院名称']",
        False,
    ] = None,
) -> CourtCode:
    """
    根据法院名称或者法院代字查询法院代字等相关数据
    """
    need_fields = target_property if target_property else []
    need_fields = need_fields if check_target_property(get_table_property_list("court_code"), need_fields) else []
    query_conds = {}
    if court_name:
        search_key = "法院名称"
        search_value = court_name
    if court_code:
        search_key = "法院代字"
        search_value = court_code
    query_conds[search_key] = search_value

    params = {"query_conds": query_conds, "need_fields": need_fields}
    api_result = http_api_call("get_court_code", params)

    if type(api_result) == dict:
        refined_answer = "根据{}是{}查询到:{}".format(search_key, search_value, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "无法根据{}是{}查询到法院信息".format(search_key, search_value)
        call_api_successfully = False

    tool_result = {
        "condition": search_value,
        "api": "get_court_code",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
