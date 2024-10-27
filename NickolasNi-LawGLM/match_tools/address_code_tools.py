from typing import Annotated, List
from match_tools.schema import AddrCode, AddrCodeEnum


from match_tools.tools_register import register_tool
from match_tools.schema import get_table_property_list
from utils import parse_json_from_response, check_target_property
from apis.api import http_api_call


@register_tool
def get_address_code(
    province: Annotated[str, "省份,直辖市的省份就天该市,比如上海市、北京市、天津市、重庆市", True],
    city: Annotated[str, "城市", True],
    district: Annotated[str, "区县", True],
    target_property: Annotated[
        List[AddrCodeEnum],
        "通用地址编码表的字段列表，比如询问某省市区的区县登记的区划代码时，需要填入['区县区划代码']",
        False,
    ] = None,
) -> AddrCode:
    """
    根据省市区查询区划代码，当地址是直辖时'省份'和'城市'都填写该市'区县'填写区。比如'重庆市南岸区'，省份是重庆市、城市是重庆市、区县是南岸区
    """
    need_fields = target_property if target_property else []
    need_fields = need_fields if check_target_property(get_table_property_list("addr_code"), need_fields) else []
    params = {"query_conds": {"省份": province, "城市": city, "区县": district}, "need_fields": need_fields}
    api_result = http_api_call("get_address_code", params)

    if type(api_result) == dict:
        refined_answer = "根据{}{}{}查询到:{}".format(province, city, district, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "根据{}{}{}无法查询到区划代码信息".format(province, city, district)
        call_api_successfully = False

    tool_result = {
        "condition": [province, city, district],
        "api": "get_address_code",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
