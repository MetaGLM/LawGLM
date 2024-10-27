from typing import get_origin, Annotated, Union, List, Optional
from match_tools.schema import CompanyInfo, SubCompanyInfo, LegalDocument, CompanyRegister
from match_tools.schema import (
    CompanyInfoEnum,
    SubCompanyInfoEnum,
    LegalDocumentEnum,
    CompanyRegisterEnum,
    CompanyNameCodeEnum,
)


from match_tools.tools_register import register_tool
from apis.api import augment_company_name, http_api_call
from model import call_glm
from utils import parse_json_from_response

prompt_check_company_info_args = """请对用户输入的公司信息进行判断和修正。判断公司信息的类型，包含三种:公司名称,股票代码和统一社会信用代码。股票代码由6位纯数字组成,如300682。统一社会信用代码由18位数字和字母组成,如91320722MA27RF9U87,91310114312234914L.
错误类型包含但不限于：重复的叠字，错别字。
如果用户输入的公司信息正确则fixed_info的值就是用户输入的公司信息，但仍需判断类型。

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙龙元建设集团股份有限公司
```json
{{"type":"公司名称","fixed_info":"龙元建设集团股份有限公司"}}
``` 

example：信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司
```json
{{"type":"公司名称","fixed_info":"信息产业电子第十一设计研究院科技工程股份有限公司"}}
``` 

example：陕西建设机械股份有限公公
```json
{{"type":"公司名称","fixed_info":"陕西建设机械股份有限公司"}}
``` 

example：河南龙马环境产业有有有有限限限限公公公公司司司司
```json
{{"type":"公司名称","fixed_info":"河南龙马环境产业有限公司"}}
``` 

example：温洲明鹿基础设施投资有限公司
```json
{{"type":"公司名称","fixed_info":"温州明鹿基础设施投资有限公司"}}
``` 

example：山东省戴瑞克新材料有限公司
```json
{{"type":"公司名称","fixed_info":"山东戴瑞克新材料有限公司"}}
``` 

example：330000116644
```json
{{"type":"股票代码","fixed_info":"300164"}}
``` 

example：91320722MA27RF9U87
```json
{{"type":"统一社会信用代码","fixed_info":"91320722MA27RF9U87"}}
``` 
"""


@register_tool
def get_company_info(
    key: Annotated[CompanyNameCodeEnum, "公司名称、公司简称或者公司代码_股票代码的字段名称", True],
    value: Annotated[str, "公司名称、公司简称或者公司代码_股票代码字段的具体值", True],
    target_property: Annotated[
        List[CompanyInfoEnum],
        "上市公司基本信息表的字段列表，当问题指出该表特定字段以及后续问题所用到字段时填写，比如询问某公司的法人信息时，需要填入['法人代表']，注意问题中询问字段同义转成company_info字段,比如询问上市时间对应上市日期,股票代码对应'公司代码_股票代码',董事会秘书对应董秘，比如后续问题问到子公司时，需要填入['公司名称'](根据公司名搜索子公司信息)。必须从company_info表的字段中选择，不能超出范围。该字段的选择必须非常确定，如果不传入本参数。",
        False,
    ] = None,
    # target_property: Annotated[List[CompanyInfoEnum], "上市公司基本信息表的字段列表，当问题指出该表特定字段时填写，比如询问某公司的法人信息时，需要填入['法人代表']。有如下字段可选：公司名称,公司简称,英文名称,关联证券,公司代码_股票代码,曾用简称,所属市场,所属行业,成立日期,上市日期,法人代表,总经理,董秘,邮政编码,注册地址,办公地址,联系电话,传真,官方网址,电子邮箱,入选指数,主营业务,经营范围,机构简介,每股面值,首发价,首发募资净额,首发主承销商", False] = None
) -> CompanyInfo:
    """
    根据公司名称或者公司代码_股票代码获得如下信息：公司名称, 公司简称, 英文名称, 关联证券, 公司代码_股票代码, 曾用简称, 所属市场, 所属行业, 成立日期, 上市日期, 法人代表, 总经理 ,董秘, 邮政编码, 注册地址, 办公地址, 联系电话, 传真, 官方网址, 电子邮箱, 入选指数, 主营业务, 经营范围, 机构简介, 每股面值, 首发价, 首发募资净额, 首发主承销商。
    当问'法定代表人'时必须用本工具查询的'法人代表'
    """
    if key.__contains__("代码"):
        key = "公司代码"
    need_fields = target_property if target_property else []
    if need_fields and not "公司名称" in need_fields:
        need_fields.append("公司名称")
    if "公司代码_股票代码" in need_fields:
        need_fields.remove("公司代码_股票代码")
        need_fields.append("公司代码")
    params = {"query_conds": {key: value}, "need_fields": need_fields}
    api_result = http_api_call("get_company_info", params)

    if type(api_result) == dict and len(api_result["return"]):
        if "公司代码" in api_result["return"][0].keys():
            api_result["return"][0]["公司代码_股票代码"] = api_result["return"][0]["公司代码"]
            del api_result["return"][0]["公司代码"]
        refined_answer = "根据{}是{}查询到上市公司信息:{}".format(key, value, api_result["return"][0])
        call_api_successfully = True
    else:
        return check_company_name(value, need_fields)

    tool_result = {
        # 'condition':[key, value],
        "condition": value,
        "api": "get_company_info",
        "search_result": api_result["return"][0]
        if (len(api_result["return"]) and type(api_result["return"][0]) == dict)
        else None,
        "refined_answer": refined_answer,
        "api_result": api_result,
        "call_api_successfully": call_api_successfully,
    }
    return tool_result


def check_company_name(value, need_fields):
    messages = [{"role": "system", "content": prompt_check_company_info_args}, {"role": "user", "content": value}]
    response = call_glm(messages, model="glm-4-0520", temperature=0.11, top_p=0.11)
    company_info = parse_json_from_response(response.choices[0].message.content)

    if company_info.get("type", "") == "公司名称":
        params = {"query_conds": {"公司名称": company_info.get("fixed_info", "")}, "need_fields": need_fields}
        api_result = http_api_call("get_company_info", params)

        if type(api_result) == dict and len(api_result["return"]):
            if "公司代码" in api_result["return"][0].keys():
                api_result["return"][0]["公司代码_股票代码"] = api_result["return"][0]["公司代码"]
                del api_result["return"][0]["公司代码"]
            refined_answer = "根据公司名称是{}查询到上市公司信息:{}".format(
                company_info.get("fixed_info", ""), api_result["return"][0]
            )
            call_api_successfully = True
        else:
            refined_answer = "无法根据公司名称是{}查询到上市公司信息。{}不是上市公司。".format(
                company_info.get("fixed_info", ""), company_info.get("fixed_info", "")
            )
            call_api_successfully = False

        tool_result = {
            # 'condition':[key, value],
            "condition": company_info.get("fixed_info", ""),
            "api": "get_company_info",
            "search_result": api_result["return"][0]
            if (len(api_result["return"]) and type(api_result["return"][0]) == dict)
            else None,
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": call_api_successfully,
        }
        return tool_result
    elif company_info.get("type", "") == "统一社会信用代码":
        unified_social_credit_code = company_info.get("fixed_info", "")
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
    elif company_info.get("type", "") == "股票代码":
        stock_code = company_info.get("fixed_info", "")
        params = {"query_conds": {"公司代码": stock_code}, "need_fields": need_fields}
        api_result = http_api_call("get_company_info", params)

        if type(api_result) == dict and len(api_result["return"]):
            if "公司代码" in api_result["return"][0].keys():
                api_result["return"][0]["公司代码_股票代码"] = api_result["return"][0]["公司代码"]
                del api_result["return"][0]["公司代码"]
            refined_answer = "根据公司代码_股票代码是{}查询到上市公司信息:{}".format(
                stock_code, api_result["return"][0]
            )
            call_api_successfully = True
        else:
            refined_answer = "无法根据公司代码_股票代码是{}查询到上市公司信息。{}不是上市公司。".format(
                stock_code, stock_code
            )
            call_api_successfully = False

        tool_result = {
            "condition": stock_code,
            "api": "get_company_info",
            "search_result": api_result["return"][0]
            if (len(api_result["return"]) and type(api_result["return"][0]) == dict)
            else None,
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": call_api_successfully,
        }
        return tool_result
