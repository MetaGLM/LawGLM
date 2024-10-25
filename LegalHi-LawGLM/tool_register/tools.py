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


# Tool Definitions
def http_api_call(api_name, data):
    url = f"{domain}/law_api/s1_b/{api_name}"
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp
    # print("该接口的输出结果为: ", final_rsp)
    return {"输出结果总长度": len(final_rsp), "输出结果": final_rsp}


@register_tool
def get_company_info(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> CompanyInfo:
    """
    根据上市公司名称、简称或代码查找上市公司信息。
    对应表中存在以下字段信息: ["公司名称", "公司简称", "英文名称", "关联证券", "公司代码", "曾用简称", "所属市场", "所属行业", "上市日期", "法人代表", "总经理", "董秘", "邮政编码", "注册地址", "办公地址", "联系电话", "传真", "官方网址", "电子邮箱", "入选指数", "主营业务", "经营范围", "机构简介", "每股面值", "首发价格", "首发募资净额", "首发主承销商"]
    示例输入：{"query_conds": {"公司名称": " "}, "need_fields": ["公司代码"]}
    """
    return http_api_call("get_company_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_company_register(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> CompanyRegister:
    """
    根据公司名称，查询工商信息。
    对应表中存在以下信息:["公司名称", "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "企业简介", "经营范围"]
    示例输入：{"query_conds": {"公司名称": "天能电池集团股份有限公司"}, "need_fields": ["注册资本"]}
    """
    return http_api_call("get_company_register", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_company_register_name(
    query_conds: Annotated[dict, "统一社会信用代码", True],
    need_fields: Annotated[list, "需要的域", True],
) -> str:
    """
    根据统一社会信用代码查询公司名称。
    示例输入:{"query_conds": {"统一社会信用代码": ''}, "need_fields": ["公司名称"]}
    """
    return http_api_call("get_company_register_name", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_sub_company_info(
    query_conds: Annotated[dict, "公司名称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> SubCompanyInfo:
    """
    根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息。
    对应表中存在以下信息：["关联上市公司全称", "上市公司关系", "上市公司参股比例", "上市公司投资金额", "公司名称"]
    示例输入：{"query_conds": {"公司名称": " "}, "need_fields": ["关联上市公司全称"]}
    """
    return http_api_call("get_sub_company_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_sub_company_info_list(
    query_conds: Annotated[dict, "关联上市公司全称", True],
    need_fields: Annotated[list, "需要的域", True],
) -> List[SubCompanyInfo]:
    """
    根据关联上市公司（母公司）的名称查询该公司投资的所有子公司信息list。
    示例输入：{"query_conds": {"关联上市公司全称": " "}, "need_fields": []}
    """
    return http_api_call("get_sub_company_info_list", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_document(
    query_conds: Annotated[dict, "案号", True],
    need_fields: Annotated[list, "需要的域", True],
) -> LegalDoc:
    """
    根据案号查询裁判文书相关信息
    对应表中存在以下信息：["关联公司", "标题", "案号", "文书类型", "原告", "被告", "原告律师事务所", "被告律师事务所", "案由", "涉案金额", "判决结果", "日期", "文件名"]
    示例输入：{"query_conds": {"案号": "(2019)沪0115民初61975号"}, "need_fields": []}
    """
    return http_api_call("get_legal_document", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_document_list(
    query_conds: Annotated[dict, "关联公司", True], need_fields: Annotated[list, "需要的域", True]
) -> List[LegalDoc]:
    """
    根据关联公司查询所有裁判文书相关信息list
    对应表中存在以下信息：["关联公司", "标题", "案号", "文书类型", "原告", "被告", "原告律师事务所", "被告律师事务所", "案由", "涉案金额", "判决结果", "日期", "文件名"]
    示例输入：{"query_conds": {"关联公司": ""}, "need_fields": []}
    """
    return http_api_call("get_legal_document_list", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_court_info(
    query_conds: Annotated[dict, "法院名称", True], need_fields: Annotated[list, "需要的域", True]
) -> CourtInfo:
    """
    根据法院名称查询法院名录相关信息
    对应表中存在以下信息：["法院名称", "法院负责人", "成立日期", "法院地址", "法院联系电话", "法院官网"]
    示例输入：{"query_conds": {"法院名称": ""}, "need_fields": []}
    """
    return http_api_call("get_court_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_court_code(
    query_conds: Annotated[dict, "法院名称", True], need_fields: Annotated[list, "需要的域", True]
) -> CourtCode:
    """
    根据法院名称或者法院代字查询法院代字等相关数据
    对应表中存在以下信息：["法院名称", "行政级别", "法院级别", "法院代字", "区划代码", "级别"]
    示例输入：{"query_conds": {"法院代字": ""}, "need_fields": []}
    """
    return http_api_call("get_court_code", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_lawfirm_info(
    query_conds: Annotated[dict, "律师事务所", True], need_fields: Annotated[list, "需要的域", True]
) -> LawfirmInfo:
    """
    根据律师事务所查询律师事务所名录
    对应表中存在以下信息：["律师事务所名称", "律师事务所唯一编码", "律师事务所负责人", "事务所注册资本", "事务所成立日期", "律师事务所地址", "通讯电话", "通讯邮箱", "律所登记机关"]
    示例输入：{"query_conds": {"律师事务所名称": "爱德律师事务所"}, "need_fields": []}
    """
    return http_api_call("get_lawfirm_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_lawfirm_log(
    query_conds: Annotated[dict, "律师事务所名称", True], need_fields: Annotated[list, "需要的域", True]
) -> LawfirmLog:
    """
    根据律师事务所查询律师事务所统计数据
    对应表中存在以下信息：["律师事务所名称", "业务量排名", "服务已上市公司", "报告期间所服务上市公司违规事件", "报告期所服务上市公司接受立案调查"]
    示例输入：{"query_conds": {"律师事务所名称": "北京市金杜律师事务所"}, "need_fields": []}
    """
    return http_api_call("get_lawfirm_log", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_address_info(
    query_conds: Annotated[dict, "地址", True], need_fields: Annotated[list, "需要的域", True]
) -> AddrInfo:
    """
    根据地址查该地址对应的省份城市区县
    对应表中存在以下信息:["地址", "省份", "城市", "区县"]
    示例输入: {"query_conds": {"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}, "need_fields": []}
    """
    return http_api_call("get_address_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_address_code(
    query_conds: Annotated[dict, "省份，城市，区县", True], need_fields: Annotated[list, "需要的域", True]
) -> AddrCode:
    """
    根据省市区查询区划代码.
    对应表中存在以下信息: ["省份", "城市", "城市区划代码", "区县", "区县区划代码"]
    示例输入: {"query_conds": {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}, "need_fields": []}
    """
    return http_api_call("get_address_code", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_temp_info(
    query_conds: Annotated[dict, "省份，城市，日期", True], need_fields: Annotated[list, "需要的域", True]
) -> TempInfo:
    """
    根据日期及省份城市查询天气相关信息
    对应表中存在以下信息：["日期", "省份", "城市", "天气", "最高温度", "最低温度", "湿度"]
    示例输入：{"query_conds": {"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}, "need_fields": []}
    """
    return http_api_call("get_temp_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_legal_abstract(
    query_conds: Annotated[dict, "案号", True], need_fields: Annotated[list, "需要的域", True]
) -> LegalDoc:
    """
    根据案号查询文本摘要
    对应表中存在以下信息：["文件名", "案号", "文本摘要"]
    示例输入：{"query_conds": {"案号": "（2019）沪0115民初61975号"}, "need_fields": []}
    """
    return http_api_call("get_legal_abstract", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_xzgxf_info(
    query_conds: Annotated[dict, "案号", True], need_fields: Annotated[list, "需要的域", True]
) -> XzgxfInfo:
    """
    根据案号查询限制高消费相关信息
    对应表中存在以下信息：["限制高消费企业名称", "案号", "法定代表人", "申请人", "涉案金额", "执行法院", "立案日期", "限高发布日期"]
    示例输入： {"query_conds": {"案号": "（2018）鲁0403执1281号"}, "need_fields": [] }
    """
    return http_api_call("get_xzgxf_info", {"query_conds": query_conds, "need_fields": need_fields})


@register_tool
def get_xzgxf_info_list(
    query_conds: Annotated[dict, "限制高消费企业名称", True], need_fields: Annotated[list, "需要的域", True]
) -> List[XzgxfInfo]:
    """
    根据企业名称查询所有限制高消费相关信息list
    对应表中存在以下信息：["限制高消费企业名称", "案号", "法定代表人", "申请人", "涉案金额", "执行法院", "立案日期", "限高发布日期"]
    示例输入：{ "query_conds": {"限制高消费企业名称": "欣水源生态环境科技有限公司"}, "need_fields": [] }
    """
    return http_api_call("get_xzgxf_info_list", {"query_conds": query_conds, "need_fields": need_fields})


# 输出调用的名字，参数
# tools = get_tools()

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
    except json.JSONDecodeError as e:  # 因为太长解析不了
        try:
            match = re.search(r"\{(.*?)\}", rsp, re.DOTALL)
            if match:
                content = "[{" + match.group(1) + "}]"
                return json.loads(content)
        except:
            pass
        # print(rsp)
        raise ("Json Decode Error: {error}".format(error=e))


if __name__ == "__main__":
    # print(dispatch_tool("get_shell", {"query": "pwd"}))
    print(get_tools())
