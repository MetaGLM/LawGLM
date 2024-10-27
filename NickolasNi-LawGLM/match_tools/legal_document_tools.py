import json

from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import CompanyInfoEnum, SubCompanyInfoEnum, LegalDocumentEnum, CompanyRegisterEnum


from match_tools.tools_register import register_tool
from apis.api import augment_company_name, http_api_call, http_api_call_original
from prompts import prompt_check_company_info_args
from model import call_glm
from utils import parse_json_from_response


@register_tool
def get_legal_document(
    case_num: Annotated[
        str,
        "法律裁判文书的案号。案号通常由年份、法院代字和案件序号三部分组成，如：(2020)赣0781民初1260号、(2019)川01民终12104号。年份用括号()包裹如果没有括号请自动补上,比如:'2019苏0214民初6847号'需要变成'(2019)苏0214民初6847号'.",
        True,
    ],
    # target_property: Annotated[List[LegalDocumentEnum], "法律文书的字段列表，当问题指出该表特定字段以及后续问题所用到字段时填写，比如询问某案件中的被告律师事务所信息时，需要填入['被告律师事务所'],问到法院信息，需要填入['案号']，比如问到气温是多少时，需要填入['日期']。必须从legal_doc表的字段中选择，不能超出范围。该字段的选择必须非常确定，如果不传入本参数。也要注意问题中相近语义，如问题中涉及'案件的申请人'那么在这里是指'原告'.", False] = None
) -> LegalDocument:
    """
    根据法律裁判文书的案号查询该法律裁判文书的相关信息
    """
    # need_fields = target_property if target_property else []
    need_fields = []
    params = {
        "query_conds": {
            "案号": case_num,
        },
        "need_fields": need_fields,
    }
    api_result = http_api_call("get_legal_document", params)

    if type(api_result) == dict:
        refined_answer = "根据案号{}查询到:{}".format(case_num, api_result["return"][0])
        call_api_successfully = True
    else:
        refined_answer = "查询不到案号是{}法律裁判文书的".format(case_num)
        call_api_successfully = False

    tool_result = {
        "condition": case_num,
        "api": "get_legal_document",
        "search_result": api_result["return"][0],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result
    # return http_api_call("get_legal_document", params)


@register_tool
def get_legal_document_list(
    company_name: Annotated[List[str], "关联公司名称", True],
    # target_property: Annotated[List[LegalDocumentEnum], "法律文书信息表的字段列表，本参数是问题中涉及到法律文书信息表的字段的集合列表，包括对于法律文书信息表某些字段的限制和查询后续子问题用到的相关字段。尽可能包含更全面的字段，不要遗漏字段。比如询问'关于某公司起诉日期在2020年且作为被起诉人的涉案总金额为多少'时需要填入['被告','涉案金额','日期']；询问'审理案件的法院信息'时需要填入['案号']通过案号中法院代字的再查询法院信息；询问'原告或被告是某公司'时需要填入'原告'或者'被告'字段", False]
) -> List[LegalDocument]:
    """
    根据关联公司名称列表查询该公司涉及的所有案件即关联的法律裁判文书
    """

    # 字段target_property必须传入说明中可选列表，不能超出范围。该字段的选择必须非常确定，如果不确定可以填写。也要注意问题中相近语义，如问题中涉及'案件的申请人'那么在这里是指'原告'.
    # need_fields = target_property if target_property else []
    if type(company_name) == list and len(company_name) > 1:
        return get_legal_document_list_by_company_name_list(company_name)
    elif type(company_name) == list and len(company_name) == 1:
        company_name = company_name[0]
    need_fields = []
    params = {"query_conds": {"关联公司": company_name}, "need_fields": need_fields}
    api_result = http_api_call("get_legal_document_list", params)

    if type(api_result) == dict and api_result.get("return", []):
        refined_answer = "查询到与{}相关联的法律文书信息:{}".format(company_name, api_result["return"])
        call_api_successfully = True
    else:
        # refined_answer = '无法查询到与{}相关联的法律文书信息'.format(company_name)
        # call_api_successfully = False
        return check_company_name(company_name, need_fields)

    tool_result = {
        "condition": company_name,
        "api": "get_legal_document_list",
        "search_result": api_result["return"],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


def get_legal_document_list_by_company_name_list(company_name_list):
    all_legal_documents = []
    need_fields = []
    for company_name in company_name_list:
        params = {"query_conds": {"关联公司": company_name}, "need_fields": need_fields}
        api_result = http_api_call_original("get_legal_document_list", params)
        if type(api_result) == dict:
            api_result = [api_result]
        all_legal_documents.extend(api_result)

    api_result = {"return_items_count": len(all_legal_documents), "return": all_legal_documents}

    company_name = ",".join(company_name_list)
    if type(api_result) == dict and api_result.get("return", []):
        refined_answer = "查询到与{}相关联的法律文书信息:{}".format(company_name, api_result["return"])
        call_api_successfully = True
    else:
        refined_answer = "无法查询到与{}相关联的法律文书信息".format(company_name)
        call_api_successfully = False

    tool_result = {
        "condition": company_name,
        "api": "get_legal_document_list",
        "search_result": api_result["return"],
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


def check_company_name(value, need_fields):
    messages = [{"role": "system", "content": prompt_check_company_info_args}, {"role": "user", "content": value}]
    response = call_glm(messages, model="glm-4-0520", temperature=0.11, top_p=0.11)
    company_info = parse_json_from_response(response.choices[0].message.content)

    company_name = company_info.get("fixed_info", "")
    if company_name:
        params = {"query_conds": {"关联公司": company_name}, "need_fields": need_fields}
        api_result = http_api_call("get_legal_document_list", params)

        if type(api_result) == dict and api_result.get("return", []):
            refined_answer = "查询到与{}相关联的法律文书信息:{}".format(company_name, api_result["return"])
            call_api_successfully = True
        else:
            refined_answer = "无法查询到与{}相关联的法律文书信息".format(company_name)
            call_api_successfully = False

        tool_result = {
            "condition": company_name,
            "api": "get_legal_document_list",
            "search_result": api_result["return"],
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": call_api_successfully,
        }
        return tool_result
