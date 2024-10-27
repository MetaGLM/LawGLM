from typing import Annotated
from match_tools.schema import TempInfo

from match_tools.tools_register import register_tool
from apis.api import http_api_call
from utils import convert_date_2_answer_format


@register_tool
def get_temp_info(
    province: Annotated[str, "省份,直辖市的省份就天该市,比如上海市、北京市、天津市、重庆市", True],
    city: Annotated[str, "城市", True],
    date: Annotated[str, "日期，需要转成*年*月*日格式，如：2020年1月1日", True],
) -> TempInfo:
    """
    根据日期及省份城市查询天气相关信息
    参数date需要转成*年*月*日格式，如：2019-12-11应该变成2019年12月11日。几月几日如果是个位数不要在十位上加0，如：2020年04月03日应该变成2020年4月3日。
    """
    params = {"query_conds": {"省份": province, "城市": city, "日期": date}, "need_fields": []}
    api_result = http_api_call("get_temp_info", params)
    # return api_result

    date_with_answer_format = convert_date_2_answer_format(date)
    if type(api_result) == dict and len(api_result["return"]):
        refined_answer = "根据{}{}和{}查询到天气信息:{}".format(
            province, city, date_with_answer_format, api_result["return"][0]
        )
        call_api_successfully = True
    else:
        refined_answer = "无法根据{}{}和{}查询到天气信息。".format(province, city, date_with_answer_format)
        call_api_successfully = False

    tool_result = {
        "condition": [province, city, date_with_answer_format],
        "api": "get_temp_info",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
