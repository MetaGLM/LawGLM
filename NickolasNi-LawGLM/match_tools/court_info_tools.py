from typing import Annotated, List
from match_tools.schema import CourtInfo

from match_tools.tools_register import register_tool
from apis.api import http_api_call, http_api_call_original


@register_tool
def get_court_info(court_name: Annotated[str, "法院名称", True]) -> CourtInfo:
    """
    根据法院名称查询法院名录相关信息
    """
    params = {"query_conds": {"法院名称": court_name}, "need_fields": []}
    api_result = http_api_call("get_court_info", params)

    if type(api_result) == dict:
        refined_answer = "根据法院名称{}查询到:{}".format(court_name, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "无法查询到法院{}的信息".format(court_name)
        call_api_successfully = False

    tool_result = {
        "condition": court_name,
        "api": "get_court_info",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


# @register_tool
# def get_court_info_by_code_list(
#         court_code_list: Annotated[str, "法院代字数组", False] = None
# ) -> List[CourtInfo]:
#     """
#     根据法院代字列表查询法院信息列表
#     """
#     court_info_list = []
#     court_info_list_str = ','.join(court_code_list)
#     try:
#         court_code_obj_list = []
#         for court_code in court_code_list:
#             query_conds = {'法院代字': court_code}
#             params = {"query_conds": query_conds, "need_fields": []}
#             api_result = http_api_call_original("get_court_code", params)
#             court_code_obj_list.append(api_result)
#
#         court_names = [court_code_obj['法院名称'] for court_code_obj in court_code_obj_list]
#
#
#         for court_name in court_names:
#             params = {"query_conds": {"法院名称": court_name}, "need_fields": []}
#             api_result = http_api_call_original("get_court_info", params)
#             court_info_list.append(api_result)
#         refined_answer = '根据法院代字{}查询到:{}'.format(court_info_list_str, court_info_list)
#         call_api_successfully = True
#     except Exception as e:
#         refined_answer = '无法根据法院代字{}查询到法院信息'.format(court_info_list_str)
#         call_api_successfully = False
#         print(e)
#
#
#     tool_result = {
#         'condition': court_code_list,
#         'api': 'get_court_info_by_code_list',
#         'search_result': court_info_list,
#         'refined_answer': refined_answer,
#         'api_result': court_info_list,
#         'call_api_successfully': call_api_successfully}
#     return tool_result


if __name__ == "__main__":
    # court_code_list = ['辽01']
    # get_court_info_by_code_list(court_code_list)
    pass
