from typing import Annotated
from match_tools.schema import LegalAbstract

from match_tools.tools_register import register_tool
from apis.api import http_api_call, http_api_call_original


@register_tool
def get_legal_abstract(
    case_num: Annotated[
        str,
        "法律裁判文书的案号。案号通常由年份、法院代字和案件序号三部分组成，如：(2020)赣0781民初1260号、(2019)川01民终12104号，年份用括号()包裹",
        True,
    ],
) -> LegalAbstract:
    """
    根据法律裁判文书的案号查询文本摘要
    """
    params = {
        "query_conds": {
            "案号": case_num,
        },
        "need_fields": [],
    }
    result = http_api_call_original("get_legal_abstract", params)

    if len(result) == 0:
        case_num = case_num.replace("(", "（").replace(")", "）")
        params = {
            "query_conds": {
                "案号": case_num,
            },
            "need_fields": [],
        }
        result = http_api_call_original("get_legal_abstract", params)
    elif len(result) == 0:
        case_num = case_num.replace("（", "(").replace("）", ")")
        params = {
            "query_conds": {
                "案号": case_num,
            },
            "need_fields": [],
        }
        result = http_api_call_original("get_legal_abstract", params)

    if len(result):
        refined_answer = "根据案号{} 查询到法律文书摘要信息:{}".format(case_num, result)
        call_api_successfully = True
    else:
        refined_answer = "查询不到案号是{}的法律文书摘要".format(case_num)
        call_api_successfully = False

    tool_result = {
        "condition": case_num,
        "api": "get_legal_abstract",
        "search_result": result,
        "refined_answer": refined_answer,
        "api_result": result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
