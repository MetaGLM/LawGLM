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
def get_integrated_report() -> str:
    """
    生成整合报告
    """
    return "整合报告"
