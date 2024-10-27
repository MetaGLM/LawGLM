from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import AddrInfo
from match_tools.schema import (
    CompanyInfoEnum,
    SubCompanyInfoEnum,
    LegalDocumentEnum,
    CompanyRegisterEnum,
    CompanyNameCodeEnum,
)


from match_tools.tools_register import register_tool
from apis.api import augment_company_name, http_api_call


@register_tool
def get_address_info(
    address: Annotated[
        str,
        "公司地址、法院地址或者律师事务所地址。一般可以通过get_company_info、get_court_info或者get_lawfirm_info获取。",
        True,
    ],
) -> AddrInfo:
    """
    根据地址查该地址对应的省份城市区县
    """
    params = {"query_conds": {"地址": address}, "need_fields": []}
    api_result = http_api_call("get_address_info", params)
    # return api_result

    try:
        if type(api_result) == dict and len(api_result["return"]):
            del api_result["return"][0]["地址"]
            # address_result = api_result['return'][0].get('省份', '') + ', ' + api_result['return'][0].get('城市', '') + ', ' + api_result['return'][0].get('区县', '')
            refined_answer = "根据{}查询到:{}".format(address, api_result["return"][0])
            call_api_successfully = True
            search_result = api_result["return"][0]
        else:
            refined_answer = """无法根据{}查询省份城市区县信息。先获取以下信息后再次调用get_address_info获取省份城市区县信息。
如果是公司地址，可通过公司名称和get_company_info获取。
如果是法院地址，可通过法院名称和get_court_info获取。当然法院名称可以通过法院代字和get_court_code获取。
如果是律师事务所地址，可通过律师事务所名称和get_lawfirm_info获取。""".format(address)
            call_api_successfully = False
            search_result = refined_answer
    except:
        refined_answer = """无法根据{}查询省份城市区县信息。先获取以下信息后再次调用get_address_info获取省份城市区县信息。
        如果是公司地址，可通过公司名称和get_company_info获取。
        如果是法院地址，可通过法院名称和get_court_info获取。当然法院名称可以通过法院代字和get_court_code获取。
        如果是律师事务所地址，可通过律师事务所名称和get_lawfirm_info获取。""".format(address)
        call_api_successfully = False
        search_result = refined_answer
    tool_result = {
        "condition": address,
        "api": "get_address_info",
        "search_result": search_result,
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
