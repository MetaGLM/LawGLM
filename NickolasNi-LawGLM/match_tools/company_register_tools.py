from typing import get_origin, Annotated, Union, List, Optional
import json
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import CompanyRegisterEnum, SubCompanyInfoEnum, LegalDocumentEnum, CompanyRegisterEnum


from match_tools.tools_register import register_tool
from match_tools.schema import get_table_property_list
from apis.api import augment_company_name, http_api_call
from model import call_glm
from utils import parse_json_from_response, check_target_property
from prompts import prompt_check_company_info_args


@register_tool
def get_company_register(
    company_name: Annotated[str, "公司名称", True],
    target_property: Annotated[
        List[CompanyRegisterEnum],
        "公司工商照面信息表的字段列表.注意问题中询问字段同义转成company_register字段,比如询问工商登记的电话对应联系电话。有如下字段可选：公司名称,登记状态,统一社会信用代码,注册资本,成立日期,企业地址,联系电话,联系邮箱,注册号,组织机构代码,参保人数,行业一级,行业二级,行业三级,曾用名,企业简介,经营范围",
        False,
    ] = None,
    # target_property: Annotated[List[CompanyRegisterEnum], "公司工商照面信息表的字段列表，比如询问某公司的法人信息时，需要填入['法定代表人'].有如下字段可选：公司名称,登记状态,统一社会信用代码,法定代表人,注册资本,成立日期,企业地址,联系电话,联系邮箱,注册号,组织机构代码,参保人数,行业一级,行业二级,行业三级,曾用名,企业简介,经营范围", False] = None
) -> CompanyRegister:
    """
    根据公司名称获如下信息：公司名称,登记状态,统一社会信用代码,注册资本,成立日期,企业地址,联系电话,联系邮箱,注册号,组织机构代码,参保人数,行业一级,行业二级,行业三级,曾用名,企业简介,经营范围
    """
    need_fields = target_property if target_property else []
    need_fields = (
        need_fields if check_target_property(get_table_property_list("company_register"), need_fields) else []
    )
    params = {"query_conds": {"公司名称": company_name}, "need_fields": need_fields}
    api_result = http_api_call("get_company_register", params)

    if type(api_result) == dict and len(api_result["return"]):
        result = api_result["return"][0]
        if result.get("注册资本", ""):
            result["注册资本"] = str(float(result["注册资本"]) * 10000)
        refined_answer = "根据公司名称:{}查询到公司工商照面信息:{}".format(company_name, result)
        # refined_answer = '根据公司名称:{}查询到公司工商照面信息:{}'.format(company_name, result)
        call_api_successfully = True
    else:
        # refined_answer = '无法根据公司名称:{}查询到该公司工商照面信息'.format(company_name)
        # call_api_successfully = False
        return check_company_name(company_name, need_fields)

    tool_result = {
        "condition": company_name,
        "api": "get_company_register",
        "search_result": result,
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result

    # company_name = augment_company_name(company_name)
    # params = {"query_conds": {"公司名称": company_name}, "need_fields": []}
    # return http_api_call("get_company_register", params)


def check_company_name(value, need_fields):
    messages = [{"role": "system", "content": prompt_check_company_info_args}, {"role": "user", "content": value}]
    response = call_glm(messages, model="glm-4-0520", temperature=0.11, top_p=0.11)
    company_info = parse_json_from_response(response.choices[0].message.content)

    company_name = company_info.get("fixed_info", "")
    if company_name:
        params = {"query_conds": {"公司名称": company_name}, "need_fields": need_fields}
        api_result = http_api_call("get_company_register", params)

        if type(api_result) == dict and len(api_result["return"]):
            result = api_result["return"][0]
            if result.get("注册资本", ""):
                result["注册资本"] = str(float(result["注册资本"]) * 10000)
            refined_answer = "根据公司名称:{}查询到公司工商照面信息:{}".format(company_name, result)
            # refined_answer = '根据公司名称:{}查询到公司工商照面信息:{}'.format(company_name, result)
            call_api_successfully = True
        else:
            refined_answer = "无法根据公司名称:{}查询到该公司工商照面信息".format(company_name)
            call_api_successfully = False

        tool_result = {
            "condition": company_name,
            "api": "get_company_register",
            "search_result": result,
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": call_api_successfully,
        }
        return tool_result


@register_tool
def get_company_register_name(
    unified_social_credit_code: Annotated[str, "统一社会信用代码", True],
) -> str:
    """
    根据统一社会信用代码查询公司名称。当原本是公司名称的位置出现一串数字或者数字和字母组合，比如'91320722MA27RF9U87这家公司'、'91310114312234914L对应的公司'时，此时需要条用本tool获取公司名称再用公司名称进行接下来的逻辑链。
    """
    params = {"query_conds": {"统一社会信用代码": unified_social_credit_code}, "need_fields": []}
    api_result = http_api_call("get_company_register_name", params)

    if (
        type(api_result) == dict
        and "return" in api_result.keys()
        and len(api_result["return"]) > 0
        and api_result["return"][0].get("公司名称", "")
    ):
        company_name = api_result["return"][0].get("公司名称", "")
        refined_answer = "统一社会信用代码是{}的公司名称是{}".format(unified_social_credit_code, company_name)
        call_api_successfully = True
    else:
        refined_answer = "无法查询到统一社会信用代码是{}的公司信息".format(unified_social_credit_code)
        call_api_successfully = False

    tool_result = {
        "condition": unified_social_credit_code,
        "api": "get_company_register_name",
        "search_result": company_name,
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
