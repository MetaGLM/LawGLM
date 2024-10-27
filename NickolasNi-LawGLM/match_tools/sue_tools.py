from typing import Annotated
from match_tools.schema import TempInfo

from match_tools.tools_register import register_tool
from apis.api import http_api_call_original


@register_tool
def get_sue(
    plaintiff: Annotated[dict, "原告", True],
    defendant: Annotated[dict, "被告", True],
    sue_type: Annotated[str, "起诉状", True],
) -> str:
    """
    获取民事起诉状
    """
    params = {}
    api_result = http_api_call_original("get_citizens_sue_citizens", params)
    return api_result


@register_tool
def get_citizens_sue_citizens(
    plaintiff_name: Annotated[str, "原告姓名", True],
    plaintiff_gender: Annotated[str, "原告性别", True],
    plaintiff_birthday: Annotated[str, "原告生日", True],
    plaintiff_nationality: Annotated[str, "原告民族", True],
    plaintiff_employer: Annotated[str, "原告工作单位", True],
    plaintiff_address: Annotated[str, "原告地址", True],
    plaintiff_contact_information: Annotated[str, "原告联系方式", True],
    plaintiff_authorized_attorney: Annotated[str, "原告委托诉讼代理人", True],
    plaintiff_authorized_attorney_contact_information: Annotated[str, "原告委托诉讼代理人联系方式", True],
    defendant_name: Annotated[str, "被告姓名", True],
    defendant_gender: Annotated[str, "被告性别", True],
    defendant_birthday: Annotated[str, "被告生日", True],
    defendant_nationality: Annotated[str, "被告民族", True],
    defendant_employer: Annotated[str, "被告工作单位", True],
    defendant_address: Annotated[str, "被告地址", True],
    defendant_contact_information: Annotated[str, "被告联系方式", True],
    defendant_authorized_attorney: Annotated[str, "被告委托诉讼代理人", True],
    defendant_authorized_attorney_contact_information: Annotated[str, "被告委托诉讼代理人联系方式", True],
    claim: Annotated[str, "诉讼请求", True],
    facts_and_reasons: Annotated[str, "事实和理由", True],
    evidence: Annotated[str, "证据", True],
    court_name: Annotated[str, "法院名称", True],
    sue_date: Annotated[str, "起诉日期", True],
) -> str:
    """
    获取民事起诉状-公民起诉公民
    """
    params = {
        "原告": plaintiff_name,
        "原告性别": plaintiff_gender,
        "原告生日": plaintiff_birthday,
        "原告民族": plaintiff_nationality,
        "原告工作单位": plaintiff_employer,
        "原告地址": plaintiff_address,
        "原告联系方式": plaintiff_contact_information,
        "原告委托诉讼代理人": plaintiff_authorized_attorney,
        "原告委托诉讼代理人联系方式": plaintiff_authorized_attorney_contact_information,
        "被告": defendant_name,
        "被告性别": defendant_gender,
        "被告生日": defendant_birthday,
        "被告民族": defendant_nationality,
        "被告工作单位": defendant_employer,
        "被告地址": defendant_address,
        "被告联系方式": defendant_contact_information,
        "被告委托诉讼代理人": defendant_authorized_attorney,
        "被告委托诉讼代理人联系方式": defendant_authorized_attorney_contact_information,
        "诉讼请求": claim,
        "事实和理由": facts_and_reasons,
        "证据": evidence,
        "法院名称": court_name,
        "起诉日期": sue_date,
    }
    api_result = http_api_call_original("get_citizens_sue_citizens", params)
    return api_result
