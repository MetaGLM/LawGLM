import requests
from tool_register.register import register_tool, get_tools
from typing import get_origin, Annotated, Union, List, Optional
from tool_register.schema import *
from zhipuai import ZhipuAI
import json, re

# api_list = [
#     "get_company_info",
#     "get_company_register",
#     "get_company_register_name",
#     "get_sub_company_info",
#     "get_sub_company_info_list",
#     "get_legal_document",
#     "get_legal_document_list",
#     "get_court_info",
#     "get_court_code",
#     "get_lawfirm_info",
#     "get_lawfirm_log",
#     "get_address_info",
#     "get_address_code",
#     'get_temp_info',
#     "get_legal_abstract",
#     "get_xzgxf_info",
#     "get_xzgxf_info_list",
#     "get_sum",
#     "rank",
#     "save_dict_list_to_word",
#     "get_citizens_sue_citizens",
#     "get_company_sue_citizens",
#     "get_citizens_sue_company",
#     "get_company_sue_company",
# ]

# api_list = [
#     "get_company_info",
#     "get_company_register",
#     "get_company_register_name",
# ]


domain = "https://comm.chatglm.cn"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 5DC959180ACBFF13D363AFFEB38F81CE3AFD8BA74746FBB1",
}


def rank(keys: List[Any], values: List[float], is_desc: bool = False):
    """
    rank keys by values
    """
    return [i[0] for i in sorted(zip(keys, values), key=lambda x: x[1], reverse=is_desc)]


# Tool Definitions
def http_api_call(api_name, data):
    url = f"{domain}/law_api/s1_b/{api_name}"

    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp
    # print("该接口的输出结果为: ", final_rsp)
    # print("\n\n")
    return {"return_items_count": len(final_rsp), "return": final_rsp}


@register_tool
def get_company_info(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> CompanyInfo:
    """
    根据上市公司名称、简称或代码查找上市公司信息
    """
    return http_api_call("get_company_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_company_register(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> CompanyRegister:
    """
    根据公司名称，查询工商信息
    """
    return http_api_call("get_company_register", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_company_register_name(
    query_conds: Annotated[dict, "统一社会信用代码", True],
    need_fields: Annotated[list, "需要的域", True],
) -> str:
    """
    根据统一社会信用代码查询公司名称
    """
    return http_api_call("get_company_register_name", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_sub_company_info(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> SubCompanyInfo:
    """
    根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息
    """
    return http_api_call("get_sub_company_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_sub_company_info_list(
    query_conds: Annotated[dict, "关联上市公司全称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> List[SubCompanyInfo]:
    """
    根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list
    """
    return http_api_call("get_sub_company_info_list", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_document(
    query_conds: Annotated[dict, "案号", True],
    need_fields: Annotated[list, "需要的域", True],
) -> LegalDoc:
    """
    根据案号查询裁判文书相关信息
    """
    return http_api_call("get_legal_document", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_document_list(
    query_conds: Annotated[dict, "关联公司", True], need_fields: Annotated[list, "需要的域", True]
) -> List[LegalDoc]:
    """
    根据关联公司查询所有裁判文书相关信息list
    """
    return http_api_call("get_legal_document_list", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_court_info(
    query_conds: Annotated[dict, "法院名称", True], need_fields: Annotated[list, "需要的域", True]
) -> CourtInfo:
    """
    根据法院名称查询法院名录相关信息
    """
    return http_api_call("get_court_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_court_code(
    query_conds: Annotated[dict, "法院名称", True], need_fields: Annotated[list, "需要的域", True]
) -> CourtCode:
    """
    根据法院名称或者法院代字查询法院代字等相关数据
    """
    return http_api_call("get_court_code", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_lawfirm_info(
    query_conds: Annotated[dict, "律师事务所", True], need_fields: Annotated[list, "需要的域", True]
) -> LawfirmInfo:
    """
    根据律师事务所查询律师事务所名录
    """
    return http_api_call("get_lawfirm_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_lawfirm_log(
    query_conds: Annotated[dict, "律师事务所名称", True], need_fields: Annotated[list, "需要的域", True]
) -> LawfirmLog:
    """
    根据律师事务所查询律师事务所统计数据
    """
    return http_api_call("get_lawfirm_log", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_address_info(
    query_conds: Annotated[dict, "地址", True], need_fields: Annotated[list, "需要的域", True]
) -> AddrInfo:
    """
    根据地址查该地址对应的省份城市区县
    """
    return http_api_call("get_address_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_address_code(
    query_conds: Annotated[dict, "省份，城市，区县", True], need_fields: Annotated[list, "需要的域", True]
) -> AddrCode:
    """
    根据省市区查询区划代码
    """
    return http_api_call("get_address_code", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_temp_info(
    query_conds: Annotated[dict, "省份，城市，日期", True], need_fields: Annotated[list, "需要的域", True]
) -> TempInfo:
    """
    根据日期及省份城市查询天气相关信息
    """
    return http_api_call("get_temp_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_abstract(
    query_conds: Annotated[dict, "案号", True], need_fields: Annotated[list, "需要的域", True]
) -> LegalDoc:
    """
    根据案号查询文本摘要
    """
    return http_api_call("get_legal_abstract", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_xzgxf_info(
    query_conds: Annotated[dict, "案号", True], need_fields: Annotated[list, "需要的域", True]
) -> XzgxfInfo:
    """
    根据案号查询限制高消费相关信息
    """
    return http_api_call("get_xzgxf_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_xzgxf_info_list(
    query_conds: Annotated[dict, "限制高消费企业名称", True], need_fields: Annotated[list, "需要的域", True]
) -> List[XzgxfInfo]:
    """
    根据企业名称查询所有限制高消费相关信息list
    """
    return http_api_call("get_xzgxf_info_list", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_sum(
    nums: Annotated[List[int] | List[float] | List[str], "[1, 2, 3, 4, 5]", True],
) -> float:
    """
    求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿，如"1万"
    """
    return http_api_call("get_sum", {"nums": nums})


@register_tool
def rank(
    keys: Annotated[List, "Any tape", True],
    values: Annotated[List[float], "", True],
    is_desc: Annotated[bool, "", True] = False,
) -> List:
    """
    排序接口，返回按照values排序的keys
    """
    return http_api_call("rank", {"keys": keys, "values": values, "is_desc": is_desc})


@register_tool
def save_dict_list_to_word(company_name: Annotated[str, "", True], dict_list: Annotated[str, "", True]):
    """
    通过传入结构化信息，制作生成公司数据报告
    """
    return http_api_call("save_dict_list_to_word", {"company_name": company_name, "dict_list": dict_list})


@register_tool
def get_citizens_sue_citizens(doc: Annotated[dict, "", True]) -> str:
    """
    搜索民事起诉状(公民起诉公民)
    """
    return http_api_call("get_citizens_sue_citizens", {"doc": doc})


@register_tool
def get_company_sue_citizens(doc: Annotated[dict, "", True]) -> str:
    """
    民事起诉状(公司起诉公民)
    """
    return http_api_call("get_company_sue_citizens", {"doc": doc})


@register_tool
def get_citizens_sue_company(doc: Annotated[dict, "", True]) -> str:
    """
    民事起诉状(公民起诉公司)
    """
    return http_api_call("get_citizens_sue_company", {"doc": doc})


@register_tool
def get_company_sue_company(doc: Annotated[dict, "", True]) -> str:
    """
    民事起诉状(公司起诉公司)
    """
    return http_api_call("get_company_sue_company", {"doc": doc})


# 输出调用的名字，参数
# tools = get_tools()


def get_tools_response(query, tools):
    messages = [
        {
            "role": "system",
            "content": "你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。",
        },
        {"role": "user", "content": query},
    ]

    client = ZhipuAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="glm-4",
        messages=messages,
        tools=tools,
        do_sample=False,
        tool_choice="auto",
    )
    function = response.choices[0].message.tool_calls[0].function
    func_args = function.arguments
    func_name = function.name
    return func_name, json.loads(func_args)


# 解析LLM生成的json
def prase_json_from_response(rsp: str):
    pattern = r"```json(.*?)```"
    rsp_json = None
    try:
        match = re.search(pattern, rsp, re.DOTALL)
        if match is not None:
            try:
                rsp_json = json.loads(match.group(1).strip())
            except:
                pass
        else:
            rsp_json = json.loads(rsp)
        return rsp_json
    except json.JSONDecodeError as e:
        raise ("Json Decode Error: {error}".format(error=e))


if __name__ == "__main__":
    # print(dispatch_tool("get_shell", {"query": "pwd"}))
    print(get_tools())
