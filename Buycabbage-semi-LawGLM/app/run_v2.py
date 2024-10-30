# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 18:55:34 2024

@author: 86187
"""

from zhipuai import ZhipuAI
import requests
import json
from court_name_pre import to_standard_name
import company_name_glm4
import casenumber_pre
import re
import API_diaoyong
import API_look1
import tools

client = ZhipuAI()
domain = "https://comm.chatglm.cn"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer black_myth_wukong",  # 团队token:D49……
}


def convert_investment_to_float(investment_str):
    # 去除可能的空格
    investment_str = investment_str.replace(" ", "")
    # 新增检查：如果字符串为空或全为空格，则返回None或抛出异常，根据需求选择
    if not investment_str.strip():
        return 0  # 或者 raise ValueError("Investment amount is empty.")
    # 检查是否包含“亿”单位
    if "亿" in investment_str:
        # 去除“亿”并转换为浮点数（假设金额都是以“亿”为单位）
        investment_without_unit = investment_str.replace("亿", "")
        # 处理可能的逗号分隔符（如果有的话）
        investment_without_comma = investment_without_unit.replace(",", "")
        return float(investment_without_comma) * 100000000  # 将“亿”转换为实际数值

    # 检查是否包含“万”单位
    elif "万" in investment_str:
        # 去除“万”并转换为浮点数（假设金额都是以“万”为单位）
        investment_without_unit = investment_str.replace("万", "")
        # 处理可能的逗号分隔符（如果有的话）
        investment_without_comma = investment_without_unit.replace(",", "")
        return float(investment_without_comma) * 10000  # 将“万”转换为实际数值
    elif "千" in investment_str:
        # 去除“万”并转换为浮点数（假设金额都是以“万”为单位）
        investment_without_unit = investment_str.replace("千", "")
        # 处理可能的逗号分隔符（如果有的话）
        investment_without_comma = investment_without_unit.replace(",", "")
        return float(investment_without_comma) * 1000  # 将“万”转换为实际数值
    # 如果没有单位，则直接尝试转换为浮点数（假设是已经格式化的数值）
    else:
        return float(investment_str)


def list_dict(input_data):
    if isinstance(input_data, dict) and "Items" in input_data:
        company_names = input_data["Items"]  # 直接从字典中获取'Items'键的值
    elif isinstance(input_data, list):
        company_names = input_data
    elif isinstance(input_data, str):
        company_names = [input_data]
    else:
        raise ValueError("Input must be a dict with an 'Items' key or a list.")
    return company_names


# 判断是否为上市公司


def check_company(company_name: str):
    rsp = company_name_glm4.check_listed_company(company_name)
    return rsp


# print(check_company('四川青石建设有限公司'))


def modify_list_with_a_and_b(lst, a, b):
    """
    根据列表中a和b的存在情况来修改列表。
    如果a和b都在列表中或者都不在列表中，则返回原始列表。
    如果a和b中只有一个在列表中，则向列表中添加另一个。

    参数:
    lst (list): 要修改的列表。
    a (object): 要检查并可能添加到列表中的值。
    b (object): 要检查并可能添加到列表中的值。

    返回:
    list: 修改后的列表。
    """
    # 检查a和b在列表中的存在情况
    a_present = a in lst
    b_present = b in lst

    # 如果a和b都在或都不在lst中，直接返回lst
    if a_present and b_present or not a_present and not b_present:
        return lst
    # 否则，检查哪一个不在lst中，并添加它
    if not a_present:
        lst.append(a)
    elif not b_present:
        lst.append(b)

    return lst


def rename_key_in_dict(input_dict, old_key, new_key):
    """
    在字典中将旧键重命名为新键。

    参数:
    - input_dict: 要修改的字典。
    - old_key: 字典中现有的键名。
    - new_key: 要设置的新键名。

    注意:
    - 如果旧键不存在于字典中，则函数不会进行任何修改。
    - 如果新键已经存在于字典中，则新键的旧值将被覆盖。
    """
    # 检查旧键是否存在于字典中
    if old_key in input_dict:
        # 将旧键的值赋给新键
        input_dict[new_key] = input_dict[old_key]
        # 删除旧键
        del input_dict[old_key]
    return input_dict


API_log = []


# ----------------------------------------------api--------------------------------------
#############之前写的tools工具不再调用此函数
def get_company_info_register(key: str, value: str, need_fields: list[str] = None) -> dict:
    global API_log
    if key == "公司名称":
        # 初始化用于记录调用API的列表
        value = company_name_glm4.standardize_company_name(value)

        api_calls = []

        # 初始化need_fields，如果为None则设为空列表
        need_fields = list_dict(need_fields) if need_fields is not None else []
        need_fields = modify_list_with_a_and_b(need_fields, "注册地址", "企业地址")
        need_fields = modify_list_with_a_and_b(need_fields, "电子邮箱", "联系邮箱")
        need_fields = modify_list_with_a_and_b(need_fields, "法人代表", "法定代表人")

        result = {}
        gs_fields = [
            "公司名称",
            "公司简称",
            "英文名称",
            "关联证券",
            "公司代码",
            "曾用简称",
            "所属市场",
            "所属行业",
            "成立日期",
            "上市日期",
            "法人代表",
            "总经理",
            "董秘",
            "邮政编码",
            "注册地址",
            "办公地址",
            "联系电话",
            "传真",
            "官方网址",
            "电子邮箱",
            "入选指数",
            "主营业务",
            "经营范围",
            "机构简介",
            "每股面值",
            "首发价格",
            "首发募资净额",
            "首发主承销商",
        ]
        reg_fields = [
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "企业简介",
            "经营范围",
        ]
        # similar_fields=['']
        # 检查是否需要调用日志API
        if not need_fields or any(item in gs_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_info"  # 注意：这里假设domain已经定义
            filtered_need_fields = [f for f in need_fields if f in gs_fields]
            data1 = {"query_conds": {key: value}, "need_fields": filtered_need_fields}

            try:
                rsp1 = requests.post(url, json=data1, headers=headers)  # 注意：这里假设headers已经定义
                # print(rsp1.json())
                rsp1.raise_for_status()
                result.update(rsp1.json())
                api_calls.append("get_company_info")
                API_log.append("get_company_info")
            except requests.exceptions.RequestException as e:
                print(f"调用日志API错误: {e}")

        # 检查是否需要调用信息API
        if not need_fields or any(item in reg_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_register"
            filtered_need_fields = [f for f in need_fields if f in reg_fields]
            data2 = {"query_conds": {key: value}, "need_fields": filtered_need_fields}
            try:
                rsp2 = requests.post(url, json=data2, headers=headers)
                rsp2.raise_for_status()
                d_rsp2 = rsp2.json()
                # print(d_rsp2)
                d_rsp2 = rename_key_in_dict(d_rsp2, "联系电话", "工商表联系电话")
                d_rsp2 = rename_key_in_dict(d_rsp2, "成立日期", "工商表成立日期")
                d_rsp2 = rename_key_in_dict(d_rsp2, "经营范围", "工商表经营范围")
                result.update(d_rsp2)
                api_calls.append("get_company_register")
                API_log.append("get_company_register")
            except requests.exceptions.RequestException as e:
                print(f"调用信息API错误: {e}")
        print(f"调用了api为{api_calls}")

        if "公司名称" not in result:
            # '法院名称'键不存在，添加键值对
            result["公司名称"] = value

        # 返回结果和API调用记录
        return result
    elif key == "公司简称" or key == "公司代码":
        # 初始化用于记录调用API的列表
        api_calls = []

        # 初始化need_fields，如果为None则设为空列表
        need_fields = list_dict(need_fields) if need_fields is not None else []
        if not isinstance(need_fields, list):
            need_fields = [need_fields]
        #  if '公司名称' not in  need_fields:
        #    need_fields.append('公司名称')
        if "公司名称" not in need_fields:
            need_fields.append("公司名称")
        need_fields = modify_list_with_a_and_b(need_fields, "注册地址", "企业地址")
        need_fields = modify_list_with_a_and_b(need_fields, "电子邮箱", "联系邮箱")
        need_fields = modify_list_with_a_and_b(need_fields, "法人代表", "法定代表人")

        result = {}
        gs_fields = [
            "公司名称",
            "公司简称",
            "英文名称",
            "关联证券",
            "公司代码",
            "曾用简称",
            "所属市场",
            "所属行业",
            "成立日期",
            "上市日期",
            "法人代表",
            "总经理",
            "董秘",
            "邮政编码",
            "注册地址",
            "办公地址",
            "联系电话",
            "传真",
            "官方网址",
            "电子邮箱",
            "入选指数",
            "主营业务",
            "经营范围",
            "机构简介",
            "每股面值",
            "首发价格",
            "首发募资净额",
            "首发主承销商",
        ]
        reg_fields = [
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "企业简介",
            "经营范围",
        ]
        # similar_fields=['']
        # 检查是否需要调用日志API
        # print(need_fields)
        # print(gs_fields)
        # print(any(item in gs_fields for item in need_fields))
        if not need_fields or any(item in gs_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_info"  # 注意：这里假设domain已经定义
            filtered_need_fields = [f for f in need_fields if f in gs_fields]
            data1 = {"query_conds": {key: value}, "need_fields": filtered_need_fields}
            try:
                rsp1 = requests.post(url, json=data1, headers=headers)  # 注意：这里假设headers已经定义
                # (rsp1.json())
                rsp1.raise_for_status()
                company_name_value = rsp1.json()["公司名称"]
                result.update(rsp1.json())

                api_calls.append("get_company_info")
                API_log.append("get_company_info")
            except requests.exceptions.RequestException as e:
                print(f"调用日志API错误: {e}")

        # 检查是否需要调用信息API
        if not need_fields or any(item in reg_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_register"
            filtered_need_fields = [f for f in need_fields if f in reg_fields]
            data2 = {"query_conds": {"公司名称": company_name_value}, "need_fields": filtered_need_fields}
            try:
                rsp2 = requests.post(url, json=data2, headers=headers)
                rsp2.raise_for_status()
                d_rsp2 = rsp2.json()
                # print(d_rsp2)
                d_rsp2 = rename_key_in_dict(d_rsp2, "联系电话", "工商表联系电话")
                d_rsp2 = rename_key_in_dict(d_rsp2, "成立日期", "工商表成立日期")
                d_rsp2 = rename_key_in_dict(d_rsp2, "经营范围", "工商表经营范围")
                result.update(d_rsp2)

                api_calls.append("get_company_register")
                API_log.append("get_company_register")
            except requests.exceptions.RequestException as e:
                print(f"调用信息API错误: {e}")
        print(f"调用了api为{api_calls}")

        if key not in result:
            # '法院名称'键不存在，添加键值对
            result[key] = value

        # 返回结果和API调用记录

        return result
    elif key == "统一社会信用代码":
        # 初始化用于记录调用API的列表
        company_name_value = get_company_register_name(value)["公司名称"]
        API_log.append("get_company_register_name")
        api_calls = []

        # 初始化need_fields，如果为None则设为空列表
        need_fields = list_dict(need_fields) if need_fields is not None else []
        if not isinstance(need_fields, list):
            need_fields = [need_fields]
        #  if '公司名称' not in  need_fields:
        #    need_fields.append('公司名称')
        need_fields = modify_list_with_a_and_b(need_fields, "注册地址", "企业地址")
        need_fields = modify_list_with_a_and_b(need_fields, "电子邮箱", "联系邮箱")
        need_fields = modify_list_with_a_and_b(need_fields, "法人代表", "法定代表人")

        result = {}
        gs_fields = [
            "公司名称",
            "公司简称",
            "英文名称",
            "关联证券",
            "公司代码",
            "曾用简称",
            "所属市场",
            "所属行业",
            "成立日期",
            "上市日期",
            "法人代表",
            "总经理",
            "董秘",
            "邮政编码",
            "注册地址",
            "办公地址",
            "联系电话",
            "传真",
            "官方网址",
            "电子邮箱",
            "入选指数",
            "主营业务",
            "经营范围",
            "机构简介",
            "每股面值",
            "首发价格",
            "首发募资净额",
            "首发主承销商",
        ]
        reg_fields = [
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "企业简介",
            "经营范围",
        ]
        # similar_fields=['']
        # 检查是否需要调用日志API
        # print(need_fields)
        # print(gs_fields)
        # print(any(item in gs_fields for item in need_fields))
        if not need_fields or any(item in gs_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_info"  # 注意：这里假设domain已经定义
            filtered_need_fields = [f for f in need_fields if f in gs_fields]
            data1 = {"query_conds": {"公司名称": company_name_value}, "need_fields": filtered_need_fields}
            try:
                rsp1 = requests.post(url, json=data1, headers=headers)  # 注意：这里假设headers已经定义
                # (rsp1.json())
                rsp1.raise_for_status()
                # company_name_value=rsp1.json()['公司名称']
                result.update(rsp1.json())

                api_calls.append("get_company_info")
                API_log.append("get_company_info")
            except requests.exceptions.RequestException as e:
                print(f"调用日志API错误: {e}")

        # 检查是否需要调用信息API
        if not need_fields or any(item in reg_fields for item in need_fields):
            url = f"{domain}/law_api/s1_b/get_company_register"
            filtered_need_fields = [f for f in need_fields if f in reg_fields]
            data2 = {"query_conds": {"公司名称": company_name_value}, "need_fields": filtered_need_fields}
            try:
                rsp2 = requests.post(url, json=data2, headers=headers)
                rsp2.raise_for_status()
                d_rsp2 = rsp2.json()
                # print(d_rsp2)
                d_rsp2 = rename_key_in_dict(d_rsp2, "联系电话", "工商表联系电话")
                d_rsp2 = rename_key_in_dict(d_rsp2, "成立日期", "工商表成立日期")
                d_rsp2 = rename_key_in_dict(d_rsp2, "经营范围", "工商表经营范围")
                result.update(d_rsp2)

                api_calls.append("get_company_register")
                API_log.append("get_company_register")
            except requests.exceptions.RequestException as e:
                print(f"调用信息API错误: {e}")
        print(f"调用了api为{api_calls}")

        if "公司名称" not in result:
            # '法院名称'键不存在，添加键值对
            result["公司名称"] = company_name_value
        if key not in result:
            # '法院名称'键不存在，添加键值对
            result[key] = value

        # 返回结果和API调用记录

        return result


# print(get_company_info_register(key='公司名称',value="安徽安科恒益药业有限公司",need_fields=['注册地址']))
# print(get_company_info_register(key='公司代码',value="688819",need_fields=['公司名称']))
# print(get_company_info_register(key='公司简称',value="海天精工",need_fields=['注册地址']))
# print(get_company_info_register(key='统一社会信用代码',value="913310007200456372",need_fields=['法定代表人']))
# print(API_log)
from datetime import datetime


def format_date(date_str):
    # 容许的日期格式
    formats = ["%Y年%m月%d日", "%Y-%m-%d", "%Y/%m/%d"]

    for fmt in formats:
        try:
            # 尝试将输入字符串按照给定的格式解析
            dt = datetime.strptime(date_str, fmt)
            # 获取日期部分
            day = dt.day
            # 如果日期是一位数，去掉前导零
            if day < 10:
                day_str = str(day)
            else:
                day_str = str(day)
            # 返回指定的输出格式
            return f"{dt.year}年{dt.month}月{day_str}日"
        except ValueError:
            # 如果不符合该格式，则继续尝试下一个格式
            continue

    # 如果所有格式都不匹配，则返回原始的日期字符串
    return date_str


# ---------------------------------------------API接口16个----------------------------------
# Tool Definitions
def http_api_call(api_name, data, max_data_len=None):
    url = f"{domain}/law_api/s1_b/{api_name}"
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp
    if max_data_len is None:
        max_data_len = len(final_rsp)
    API_log.append(api_name)
    return final_rsp


def get_company_info(key: str, value: str, need_fields: list[str] = None):
    if key == "公司名称":
        value = company_name_glm4.standardize_company_name(value)
    need_fields = list_dict(need_fields) if need_fields is not None else []
    if need_fields:
        yz_L = [
            "公司名称",
            "公司简称",
            "英文名称",
            "关联证券",
            "公司代码",
            "曾用简称",
            "所属市场",
            "所属行业",
            "成立日期",
            "上市日期",
            "法人代表",
            "总经理",
            "董秘",
            "邮政编码",
            "注册地址",
            "办公地址",
            "联系电话",
            "传真",
            "官方网址",
            "电子邮箱",
            "入选指数",
            "主营业务",
            "经营范围",
            "机构简介",
            "每股面值",
            "首发价格",
            "首发募资净额",
            "首发主承销商",
        ]
        need_fields = [i for i in need_fields if i in yz_L]

    data1 = {"query_conds": {key: value}, "need_fields": need_fields}
    api_name = "get_company_info"
    return http_api_call(api_name, data1)


def get_company_register(company_name, need_fields: list[str] = None):
    # 如果公司名称的长度是3或4个字符
    if len(company_name) == 3 or len(company_name) == 4:
        try:
            # 尝试使用 get_company_info 函数通过公司简称获取公司的全名
            # 如果成功，则将 company_name 更新为从 get_company_info 函数获取到的全名
            # 如果没有找到全名，或者发生了其他错误，使用默认值 "华域汽车" 作为备选
            company_name = get_company_info(key="公司简称", value=company_name, need_fields=["公司名称"])[0].get(
                "公司名称", company_name
            )
        except (IndexError, KeyError):
            # 如果发生 IndexError（列表索引越界），或者 KeyError（字典键不存在）
            # 则使用 pass 语句直接跳过异常处理部分
            # 这意味着如果 get_company_info 没有返回预期的结果，我们不会修改 company_name，并且程序将继续执行
            pass

    company_name = company_name_glm4.standardize_company_name(company_name)
    need_fields = list_dict(need_fields) if need_fields is not None else []
    if need_fields:
        need_fields = [i if i != "注册地址" else "企业地址" for i in need_fields]
    data1 = {"query_conds": {"公司名称": company_name}, "need_fields": need_fields}
    api_name = "get_company_register"

    result = http_api_call(api_name, data1)
    if result:
        result = result[0]
        if "公司名称" not in result:
            # '法院名称'键不存在，添加键值对
            result["公司名称"] = company_name
            result = [result] if isinstance(result, dict) else result
    return result


def get_company_register_name(credit_code, need_fields: list[str] = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"统一社会信用代码": credit_code}, "need_fields": need_fields}
    api_name = "get_company_register_name"
    return http_api_call(api_name, data1)


def get_sub_company_info(company_name, need_fields: list[str] = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"公司名称": company_name}, "need_fields": need_fields}
    api_name = "get_sub_company_info"
    return http_api_call(api_name, data1)


def get_sub_company_info_list(
        parent_company_name,
        need_fields: list[str] = None,
        only_wholly_owned: bool = False,
        investment_amount_above: float = 0.0,
):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"关联上市公司全称": parent_company_name}, "need_fields": need_fields}
    api_name = "get_sub_company_info_list"
    response = http_api_call(api_name, data1)
    # 筛选全资子公司
    if only_wholly_owned:
        response = [item for item in response if item.get("上市公司参股比例") == "100.0"]

    # 筛选投资金额大于指定数值的子公司
    if investment_amount_above > 0.0:
        response = [
            item
            for item in response
            if item.get("上市公司投资金额")
               and convert_investment_to_float(item["上市公司投资金额"]) >= investment_amount_above
        ]

    return response


def get_legal_document(case_number, need_fields: list[str] = None, include_judgment_result: bool = True):
    case_number = case_number.replace("（", "(").replace("）", ")")
    case_number = casenumber_pre.standardize_case_number(case_number)
    need_fields = list_dict(need_fields) if need_fields is not None else []
    #    if '案号' not in need_fields:
    #        need_fields.append('案号')
    data1 = {"query_conds": {"案号": case_number}, "need_fields": need_fields}
    api_name = "get_legal_document"
    rsp = http_api_call(api_name, data1)
    d_doc = rsp[0]
    if rsp:
        if not include_judgment_result:
            if "判决结果" in d_doc:
                del d_doc["判决结果"]

    return [d_doc]


def get_legal_document_list(
        related_company: str, role=None, need_fields: list = None, include_judgment_result: bool = True
):
    """
    根据关联公司查询所有裁判文书相关信息。
    参数:
    - related_company: 需要查询的关联公司名称。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个LegalDoc列表，包含与关联公司相关的所有裁判文书信息。
    """

    def add_case_year_and_rename_date(cases):
        # 检查cases是否为单个字典，如果是，则将其转换为列表
        if not isinstance(cases, list):
            cases = [cases]

        for case in cases:
            # 确保'案号'键存在
            if "案号" in case:
                # 从案号中提取年份
                match = re.search(r"\((\d{4})\)", case["案号"])
                if match:
                    case_year = match.group(1)
                    case["案件发生年度"] = case_year
                else:
                    case["案件发生年度"] = "未从案号中正确提取年度信息"
            else:
                pass  # case['案件发生年度'] = '案号信息缺失'

            # 确保'日期'键存在
            if "日期" in case:
                case["审理日期"] = case.pop("日期")  # 更改键名并移除旧键
            else:
                # 如果'日期'键不存在，可以选择不添加'审理日期'键，或者设置为某个默认值
                # 这里选择不添加，但你可以根据需要调整
                pass

        # 如果输入是单个字典，则返回单个字典（如果需要）
        # if len(cases) == 1:
        #     return cases[0]

        return cases

    need_fields1 = list_dict(need_fields) if need_fields is not None else []
    need_fields = ["日期" if item == "审理日期" else item for item in need_fields1]

    if "案件发生年度" in need_fields:
        if "案号" not in need_fields:
            need_fields.append("案号")
            need_fields = [item for item in need_fields if item != "案件发生年度"]
        else:
            need_fields = [item for item in need_fields if item != "案件发生年度"]
    if role:
        need_fields.append("原告")
        need_fields.append("被告")

    def find_cases(cases, company_name, role=None):
        """
        根据公司名称和诉讼角色查找相关案件信息。

        参数:
        - company_name (str): 公司名称。
        - role (str): 诉讼角色，可选值为 "原告" 或 "被告"。

        返回:
        - list: 包含匹配案件信息的字典列表。
        """
        # 数据源
        # cases = [{'关联公司': '国民技术股份有限公司', '标题': '顾某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事裁定书', '案号': '(2019)粤03民初2348号', '文书类型': '民事裁定书', '原告': '顾某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市元吉律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '本案按顾某某撤回起诉处理 。 ', '文件名': '（2019）粤03民初2348号.txt', '案件发生年度': '2019', '审理日期': '2019-08-19 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '贺某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事裁定书', '案号': '(2019)粤03民初2366号', '文书类型': '民事裁定书', '原告': '贺某某', '被告': '国民技术股份有限公司', '原告律师事务所': '广东尚律律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '本案按贺某某撤回起诉处理 。 ', '文件名': '（2019）粤03民初2366号.txt', '案件发生年度': '2019', '审理日期': '2019-08-19 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '赵某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事裁定书', '案号': '(2019)粤03民初261号', '文书类型': '民事裁定书', '原告': '赵某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市元吉律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '准许原告赵某某撤诉 。  \n \n案件受理费16789.77元(赵某某已预交)减半收取,由原告赵某某负担8394.89元,多预交的案件受理费由本院予以退回 。 ', '文件名': '（2019）粤03民初261号.txt', '案件发生年度': '2019', '审理日期': '2019-08-19 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '陈某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事判决书', '案号': '(2019)粤03民初265号', '文书类型': '民事判决书', '原告': '陈某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市元吉律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回原告陈某某的诉讼请求 。  \n \n案件受理费709.6元,由原告陈某某负担 。  \n \n如不服本判决,可在本判决书送达之日起十五日内,向本院递交上诉状,并按对方当事人的人数提交上诉状副本,上诉于广东省高级人民法院 。 ', '文件名': '（2019）粤03民初265号.txt', '案件发生年度': '2019', '审理日期': '2019-12-10 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '吴某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事判决书', '案号': '(2019)粤03民初3506号', '文书类型': '民事判决书', '原告': '吴某某', '被告': '国民技术股份有限公司', '原告律师事务所': '广东拓万律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回原告吴某某的诉讼请求 。  \n \n案件受理费5029.73元,由原告吴某某负担 。  \n \n如不服本判决,可在本判决书送达之日起十五日内,向本院递交上诉状,并按对方当事人的人数提交上诉状副本,上诉于广东省高级人民法院 。 ', '文件名': '（2019）粤03民初3506号.txt', '案件发生年度': '2019', '审理日期': '2020-03-05 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '蒋某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事裁定书', '案号': '(2019)粤03民初3573号', '文书类型': '民事裁定书', '原告': '蒋某某', '被告': '国民技术股份有限公司', '原告律师事务所': '广东邦仪律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '本案按蒋某某撤回起诉处理 。 ', '文件名': '（2019）粤03民初3573号.txt', '案件发生年度': '2019', '审理日期': '2019-09-23 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '汪某某与国民技术股份有限公司证券虚假陈述责任纠纷一审民事判决书', '案号': '(2019)粤03民初678号', '文书类型': '民事判决书', '原告': '汪某某', '被告': '国民技术股份有限公司', '原告律师事务所': '', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回原告汪某某的诉讼请求 。  \n \n案件受理费6494.65元,由原告汪某某负担 。  \n \n如不服本判决,可在本判决书送达之日起十五日内,向本院递交上诉状,并按对方当事人的人数提交上诉状副本,上诉于广东省高级人民法院 。 ', '文件名': '（2019）粤03民初678号.txt', '案件发生年度': '2019', '审理日期': '2019-12-10 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '国民技术股份有限公司买卖合同纠纷一审民事裁定书', '案号': '(2020)沪0115民初24668号', '文书类型': '民事裁定书', '原告': '国民技术股份有限公司', '被告': '上海众人网络安全技术有限公司', '原告律师事务所': '', '被告律师事务所': '', '案由': '买卖合同纠纷', '涉案金额': '0', '判决结果': '本案按原告国民技术股份有限公司撤回起诉处理 。 ', '文件名': '（2020）沪0115民初24668号.txt', '案件发生年度': '2020', '审理日期': '2020-05-11 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '符某某、国民技术股份有限公司劳动争议执行实施类执行裁定书', '案号': '(2020)粤0305执10219号', '文书类型': '执行裁定书', '原告': '符某某', '被告': '国民技术股份有限公司', '原告律师事务所': '广东龙新律师事务所', '被告律师事务所': '', '案由': '劳动争议', '涉案金额': '0', '判决结果': '广东省深圳市中级人民法院(2019)粤03民终25346号民事判决书中申请执行人申请执行事项已执行完毕,本案予以结案 。  \n \n本裁定送达后立即生效 。 ', '文件名': '（2020）粤0305执10219号.txt', '案件发生年度': '2020', '审理日期': '2020-08-25 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '李某某、国民技术股份有限公司证券虚假陈述责任纠纷二审民事判决书', '案号': '(2020)粤民终1128号', '文书类型': '民事判决书', '原告': '李某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市德渊律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回上诉,维持原判 。  \n \n二审案件受理费106575.77元,由李某某负担 。  \n \n本判决为终审判决 。 ', '文件名': '（2020）粤民终1128号.txt', '案件发生年度': '2020', '审理日期': '2020-11-23 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '高某某、国民技术股份有限公司证券虚假陈述责任纠纷二审民事判决书', '案号': '(2020)粤民终1129号', '文书类型': '民事判决书', '原告': '高某某', '被告': '国民技术股份有限公司', '原告律师事务所': '江苏维尔达律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回上诉,维持原判 。  \n \n二审案件受理费6990.95元,由高某某负担 。  \n \n本判决为终审判决 。 ', '文件名': '（2020）粤民终1129号.txt', '案件发生年度': '2020', '审理日期': '2020-11-23 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '陈某某、国民技术股份有限公司证券虚假陈述责任纠纷二审民事裁定书', '案号': '(2020)粤民终1130号', '文书类型': '民事裁定书', '原告': '陈某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市元吉律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '准许陈某某撤回上诉 。 一审判决自本裁定书送达之日起发生法律效力 。  \n \n二审案件受理费709.6元,减半收取354.8元,由陈某某负担 。 陈某某预交的二审案件受理费709.6元,由本院退回陈某某354.8元 。  \n \n本裁定为终审裁定 。 ', '文件名': '（2020）粤民终1130号.txt', '案件发生年度': '2020', '审理日期': '2020-11-23 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '窦某某、国民技术股份有限公司证券虚假陈述责任纠纷二审民事判决书', '案号': '(2020)粤民终1131号', '文书类型': '民事判决书', '原告': '窦某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京市雄志律师事务所', '被告律师事务所': '广东深天成律师事务所', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回上诉,维持原判 。  \n \n二审案件受理费45263.19元,由窦某某负担 。  \n \n本判决为终审判决 。 ', '文件名': '（2020）粤民终1131号.txt', '案件发生年度': '2020', '审理日期': '2020-11-23 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '李某某、国民技术股份有限公司证券虚假陈述责任纠纷其他民事民事裁定书', '案号': '(2021)最高法民申3787号', '文书类型': '民事裁定书', '原告': '李某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京卓海律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回李某某的再审申请 。 ', '文件名': '（2021）最高法民申3787号.txt', '案件发生年度': '2021', '审理日期': '2021-07-29 00:00:00'}, {'关联公司': '国民技术股份有限公司', '标题': '窦某某、国民技术股份有限公司证券虚假陈述责任纠纷其他民事民事裁定书', '案号': '(2021)最高法民申4211号', '文书类型': '民事裁定书', '原告': '窦某某', '被告': '国民技术股份有限公司', '原告律师事务所': '北京中登律师事务所', '被告律师事务所': '', '案由': '证券虚假陈述责任纠纷', '涉案金额': '0', '判决结果': '驳回窦某某的再审申请 。 ', '文件名': '（2021）最高法民申4211号.txt', '案件发生年度': '2021', '审理日期': '2021-06-30 00:00:00'}]

        if role in ["原告", "被告"]:
            # 筛选条件
            # print(cases)
            filter_condition = lambda x: role in ["原告", "被告"] and company_name in x[role]

            # 根据条件筛选案件
            filtered_cases = list(filter(filter_condition, cases))
        else:
            filtered_cases = cases

        return filtered_cases

    need_fields = list_dict(need_fields) if need_fields is not None else []
    need_fields = []
    # related_company=company_name_glm4.standardize_company_name_1(related_company)
    # need_fields=['关联公司', '标题', '案号', '文书类型', '原告', '被告', '原告律师事务所', '被告律师事务所', '案由', '涉案金额', '判决结果', '审理日期', '案件发生年度', '文件名']
    data1 = {"query_conds": {"关联公司": related_company}, "need_fields": need_fields}
    api_name = "get_legal_document_list"
    rsp = http_api_call(api_name, data1)

    if need_fields:
        filtered_results = [{key: item[key] for key in need_fields if key in item} for item in rsp]
        filtered_results = add_case_year_and_rename_date(filtered_results)
    else:
        filtered_results = rsp
        filtered_results = add_case_year_and_rename_date(filtered_results)
    filtered_results = find_cases(filtered_results, related_company, role=role)

    def remove_judgment_results(documents):
        for document in documents:
            if "判决结果" in document:
                del document["判决结果"]
        return documents

    if filtered_results:
        if not include_judgment_result:
            filtered_results = remove_judgment_results(filtered_results)
    return filtered_results


# print(get_legal_document_list('伊吾广汇矿业有限公司'))
# print(get_legal_document_list(**{"related_company": "伊吾广汇矿业有限公司", "role": "被告", "need_fields": ["案号", "涉案金额"]}))


def get_court_info(court_name, need_fields: list[str] = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"法院名称": court_name}, "need_fields": need_fields}
    api_name = "get_court_info"
    rsp = http_api_call(api_name, data1)
    if not rsp:
        court_name = to_standard_name(court_name)
        data1 = {"query_conds": {"法院名称": court_name}, "need_fields": need_fields}
        rsp = http_api_call(api_name, data1)
        return rsp
    return rsp


def get_court_code(key: str, value: str, need_fields: list[str] = None):
    if key == "案号":
        value = casenumber_pre.extract_court_code(value)
        key = "法院代字"
    if key == "法院名称":
        value = to_standard_name(value)

    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {key: value}, "need_fields": need_fields}
    api_name = "get_court_code"
    return http_api_call(api_name, data1)


def get_lawfirm_info(lawfirm_name, need_fields: list[str] = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"律师事务所名称": lawfirm_name}, "need_fields": need_fields}
    api_name = "get_lawfirm_info"
    return http_api_call(api_name, data1)


def get_lawfirm_log(lawfirm_name, need_fields: list[str] = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"律师事务所名称": lawfirm_name}, "need_fields": need_fields}
    api_name = "get_lawfirm_log"
    return http_api_call(api_name, data1)


# 11
def get_address_info(address: str, need_fields: list = None) -> dict:
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"地址": address}, "need_fields": need_fields}
    api_name = "get_address_info"
    return http_api_call(api_name, data1)


# print(get_address_info("新民市辽河大街12号", []))


# 12
def get_address_code(province: str, city: str, district: str, need_fields: list = None) -> dict:
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"省份": province, "城市": city, "区县": district}, "need_fields": need_fields}
    api_name = "get_address_code"
    return http_api_call(api_name, data1)


# print(get_address_code("山东省","济宁市","嘉祥县"))


def get_temp_info(province: str, city: str, date: str, need_fields: list = None) -> dict:
    if date:
        date = format_date(date)
    need_fields = list_dict(need_fields) if need_fields is not None else []
    data1 = {"query_conds": {"省份": province, "城市": city, "日期": date}, "need_fields": need_fields}
    api_name = "get_temp_info"
    return http_api_call(api_name, data1)


# get_temp_info(**{"date": "2020年1月4日", "province": "北京市", "city": "北京市"})


# 14
def get_legal_abstract(case_number: str, need_fields: list = None):
    case_number = case_number.replace("(", "（").replace(")", "）")
    # case_number=casenumber_pre.standardize_case_number(case_number)
    need_fields = list_dict(need_fields) if need_fields is not None else []
    #    if '案号' not in need_fields:
    #        need_fields.append('案号')
    data1 = {"query_conds": {"案号": case_number}, "need_fields": need_fields}
    api_name = "get_legal_abstract"
    return http_api_call(api_name, data1)


# print(get_legal_abstract('（2019）兵08财保8号'))


# 15
def get_xzgxf_info(case_number: str, need_fields: list = None) -> dict:
    case_number = case_number.replace("(", "（").replace(")", "）")
    need_fields = list_dict(need_fields) if need_fields is not None else []

    data1 = {"query_conds": {"案号": case_number}, "need_fields": need_fields}
    api_name = "get_xzgxf_info"
    return http_api_call(api_name, data1)


# print(get_xzgxf_info('（2018）鲁0403执1281号',["限制高消费企业名称"]))
# print(get_legal_document('(2019)沪0115民初61975号'))


# 16
def get_xzgxf_info_list(company_name: str, need_fields: list = None):
    need_fields = list_dict(need_fields) if need_fields is not None else []

    data1 = {"query_conds": {"限制高消费企业名称": company_name}, "need_fields": need_fields}
    api_name = "get_xzgxf_info_list"
    return http_api_call(api_name, data1)


# 17
def get_lawfirm_info_log(lawfirm_name: str, need_fields: list[str] = None) -> dict:
    # 初始化need_fields，如果为None则设为空列表
    need_fields = list_dict(need_fields) if need_fields is not None else []
    result = {}
    log_fields = ["业务量排名", "服务已上市公司", "报告期间所服务上市公司违规事件", "报告期所服务上市公司接受立案调查"]
    info_fields = [
        "律师事务所唯一编码",
        "律师事务所负责人",
        "事务所注册资本",
        "事务所成立日期",
        "律师事务所地址",
        "通讯电话",
        "通讯邮箱",
        "律所登记机关",
    ]
    if not need_fields or any(item in log_fields for item in need_fields):
        filtered_need_fields = [f for f in need_fields if f in log_fields]
        # print('---------------')
        # print(filtered_need_fields)
        rsp_log = get_lawfirm_log(lawfirm_name, filtered_need_fields)
        if rsp_log:
            # 如果rsp_log不为空，则更新result
            result.update(rsp_log[0])  # 假设rsp_log的第一个元素是一个字典

    # 检查是否需要调用信息API
    if not need_fields or any(item in info_fields for item in need_fields):
        filtered_need_fields = [f for f in need_fields if f in info_fields]
        rsp_info = get_lawfirm_info(lawfirm_name, filtered_need_fields)
        # print('---------------')
        # print(filtered_need_fields)
        if rsp_info:
            result.update(rsp_info[0])
    # 返回结果和API调用记录
    if "律师事务所名称" not in result:
        # '法院名称'键不存在，添加键值对
        result["律师事务所名称"] = lawfirm_name
    return result


# company_name='朗新科技集团股份有限公司'
def get_zgsmugs_cases(company_name):
    zgsxx = get_sub_company_info_list(company_name)
    zgs_names = [i["公司名称"] for i in zgsxx]
    # zgsxx_dict={'子公司信息': zgsxx}
    # dict_list['子公司信息'] = zgsxx_dict['子公司信息']
    L_mgs_zgs = []
    cpwsxx_mgs = get_legal_document_list(company_name, include_judgment_result=True)
    L_mgs_zgs = L_mgs_zgs + cpwsxx_mgs
    for zgs_name in zgs_names:
        cpwszz_zgs = get_legal_document_list(zgs_name, include_judgment_result=True)
        if not isinstance(cpwszz_zgs, list):
            cpwszz_zgs = [cpwszz_zgs]
        L_mgs_zgs = L_mgs_zgs + cpwszz_zgs

    # cpwsxxs=filter_cases_by_criteria(L_mgs_zgs,year=year, amount_min=amount_min, amount_max=amount_max)
    cpwsxxs = L_mgs_zgs
    cpwsxx_list = cpwsxxs
    # exclude_litigation_fields=['判决结果']

    # cpwsxx_list.append(
    #    {'关联公司':cpwsxx.get('关联公司'),
    #      '原告': cpwsxx.get('原告'),
    #     '被告': cpwsxx.get('被告'),
    #     '案由': cpwsxx.get( '案由'),
    #     '涉案金额':str_to_float_or_original(cpwsxx.get('涉案金额')),
    #     '日期':str_to_timestamp(cpwsxx.get('审理日期'))
    #      })

    cpwsxx_dict = {"裁判文书": cpwsxx_list}
    return cpwsxx_dict


# get_zgsmugs_cases('')
# get_company_info('公司代码','300682')


# dict_list['裁判文书'] = cpwsxx_dict['裁判文书']
# print(get_lawfirm_info_log('爱德律师事务所'))

# print(get_lawfirm_info_log(**{"lawfirm_name": "爱德律师事务所", "need_fields": ["律师事务所地址"]}))

# LL=get_xzgxf_info_list('吉艾科技集团股份公司')


# print(get_company_info(key='公司名称',value="上海妙可蓝多食品科技股份有限公司",need_fields=[]))

# print(get_company_register("上海妙可蓝多食品科技股份有限公司"))

# print(get_company_register_name('913401007885810000'))
# print(get_temp_info(**{"province": "北京市", "city": "北京市", "date": "2020年1月1日"}))

# print(get_lawfirm_log('北京市金杜律师事务所'))
# print(get_lawfirm_info('上海申浩（成都）律师事务所'))

# print(get_court_info_code(key='法院代字',value="苏0481",need_fields=['区县']))

# print(get_court_info_code(key='法院名称',value="四川省眉山市中级人民法院",need_fields=['区县']))


# print(get_court_info("江西省赣州市中级人民法院"))

# print(get_court_code(key='法院代字',value="苏0481"))
# print(get_lawfirm_info('上海申浩（成都）律师事务所'))

# print(get_company_info('公司名称', '安徽皖仪科技股份有限公司'))
# print(get_company_register('安徽皖仪科技股份有限公司'))
# print(get_company_register_name('913305007490121183'))
# print(get_sub_company_info('上海爱斯达克汽车空调系统有限公司'))


# print(get_sub_company_info_list('安徽皖仪科技股份有限公司'))
# print((case_number="(2021)京0108民初8641号",need_fields="原告"))
# print(get_legal_document_list("山东省戴瑞克新材料有限公司",[]))
# print(get_legal_document_list("国民技术股份有限公司"))


'''

#10
def get_lawfirm_log(lawfirm_name: str, need_fields: list[str] = None) -> dict:
    """
    根据律师事务所名称查询律师事务所统计数据。
    参数:
    - lawfirm_name: 需要查询的律师事务所名称。
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。
    返回:
    - 返回一个字典，包含律师事务所统计数据。
    """
    url = f"{domain}/law_api/s1_b/get_lawfirm_log"
    data = {"query_conds": {"律师事务所名称": lawfirm_name}, "need_fields": need_fields or []}
    try:
        rsp = requests.post(url, json=data, headers=headers)
        rsp.raise_for_status()
        return rsp.json()
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return {}
get_lawfirm_log('北京市金杜律师事务所')
'''
# API优化9-10
'''
def get_lawfirm_info_log(lawfirm_name: str, need_fields: list[str] = None) -> dict:  
    """  
    根据律师事务所名称和需要的字段查询律师事务所的日志和统计信息。  
  
    参数:  
    - lawfirm_name: 需要查询的律师事务所名称。  
    - need_fields: 需要返回的字段列表，如果为None则返回所有字段。  
  
    返回:  
    - 返回一个字典，包含律师事务所的日志和统计信息。  
    - 同时返回一个列表，记录调用了哪些API。  
    """  
    # 初始化用于记录调用API的列表  
    api_calls = []  
  
    # 初始化need_fields，如果为None则设为空列表  
    need_fields = list_dict(need_fields) if need_fields is not None else []  
  
    result = {}  
    log_fields = ["业务量排名", "服务已上市公司", "报告期间所服务上市公司违规事件", "报告期所服务上市公司接受立案调查"]  
    info_fields = ["律师事务所唯一编码", "律师事务所负责人", "事务所注册资本", "事务所成立日期", "律师事务所地址", "通讯电话", "通讯邮箱", "律所登记机关"]  
  
    # 检查是否需要调用日志API  
    if not need_fields or any(item in log_fields for item in need_fields):  
        url = f"{domain}/law_api/s1_b/get_lawfirm_log"  # 注意：这里假设domain已经定义  
        filtered_need_fields = [f for f in need_fields if f in log_fields]  
        data1 = {"query_conds": {"律师事务所名称": lawfirm_name}, "need_fields": filtered_need_fields}  
        print(data1)
        try:  
            rsp1 = requests.post(url, json=data1, headers=headers)  # 注意：这里假设headers已经定义  
            rsp1.raise_for_status()  
            result.update(rsp1.json())  
            api_calls.append("get_lawfirm_log")  
        except requests.exceptions.RequestException as e:  
            print(f"调用日志API错误: {e}")  
  
    # 检查是否需要调用信息API  
    if not need_fields or any(item in info_fields for item in need_fields):  
        url = f"{domain}/law_api/s1_b/get_lawfirm_info"  
        filtered_need_fields = [f for f in need_fields if f in info_fields]  
        data2 = {"query_conds": {"律师事务所名称": lawfirm_name}, "need_fields": filtered_need_fields}  
        try:  
            rsp2 = requests.post(url, json=data2, headers=headers)  
            rsp2.raise_for_status()  
            result.update(rsp2.json())  
            api_calls.append("get_lawfirm_info")  
        except requests.exceptions.RequestException as e:  
            print(f"调用信息API错误: {e}")  
    print(f'调用了api为{api_calls}')
    
    # 返回结果和API调用记录
    if '律师事务所名称' not in result:
        # '法院名称'键不存在，添加键值对
        result['律师事务所名称'] =lawfirm_name
    return result
'''


# print(get_lawfirm_info_log('上海申浩（成都）律师事务所'))


# 通用的API请求函数
def request_api(url, data):
    try:
        rsp = requests.post(url, json=data, headers=headers)
        rsp.raise_for_status()
        return rsp.json()
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        return {}
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        return {}
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"OOps: Something Else: {err}")
        return {}


#  判断是否限制高消费
def check_restriction_and_max_amount(company_name):
    # 检查列表是否为空
    LL = get_xzgxf_info_list(company_name)

    if not LL:
        return f"{company_name}没有限制高消费的记录"
    # 确保所有记录都有'涉案金额'字段且可以转换为数字，过滤掉不合规的记录
    valid_records = [record for record in LL if "涉案金额" in record and record["涉案金额"] != "-"]

    # 如果有效记录存在，则找出涉案金额最大值
    if valid_records:
        max_amount_record = max(valid_records, key=lambda x: float(x["涉案金额"]))
        # print(max_amount_record)
        restriction_and_max_amount = {
            "限制高消费企业名称": company_name,
            "案号": max_amount_record["案号"],
            "最大涉案金额": max_amount_record["涉案金额"],
        }
        return restriction_and_max_amount
    else:
        # 如果所有记录的涉案金额都是'-', 表示没有具体金额信息
        return f"{company_name}有限制高消费的记录，但无具体涉案金额信息"


# 测试函数
# aa= check_restriction_and_max_amount('吉艾科技集团股份公司')
# print(aa)


def calculate_total_amount_and_count_simple(company_name):
    """
    计算指定公司名下所有记录的次数，并汇总有效涉案金额。

    :param company_name: 公司名称
    :return: 包含总涉案金额和总记录次数的字典
    """
    # 获取信息列表
    LL = get_xzgxf_info_list(company_name)

    if not LL:
        return f"{company_name}没有相关记录"

    # 初始化总金额和总次数
    total_amount = 0
    total_count = len(LL)  # 只要有记录就算一次

    # 计算有效涉案金额的总和
    for record in LL:
        if "涉案金额" in record and record["涉案金额"] != "-":
            total_amount += float(record["涉案金额"])

    # 返回结果
    return {"限制高消费企业名称": company_name, "限高涉案总金额": total_amount, "限高总数": f"{total_count}次"}


# aa= calculate_total_amount_and_count_simple('吉艾科技集团股份公司')
# print(aa)


# 17
def get_cishu(company, year=None):
    cases = get_legal_document_list(company)
    # 初始化所有变量
    qcount_zcs = 0
    qcount_plaintiff = 0
    qcount_defendant = 0
    qtotal_amount = 0.0
    qamount_plaintiff = 0.0
    qamount_defendant = 0.0

    count_zcs = 0
    count_plaintiff = 0
    count_defendant = 0
    total_amount = 0.0
    amount_plaintiff = 0.0
    amount_defendant = 0.0
    # 如果没有指定年份，则统计所有案件
    if year is None:
        qcount_zcs = len(cases)
        qcount_plaintiff = sum(1 for case in cases if company in case["原告"])
        qcount_defendant = sum(1 for case in cases if company in case["被告"])
        qtotal_amount = sum(float(case["涉案金额"]) for case in cases)
        qamount_plaintiff = sum(float(case["涉案金额"]) for case in cases if company in case["原告"])
        qamount_defendant = sum(float(case["涉案金额"]) for case in cases if company in case["被告"])
    else:
        # 如果指定了年份，则只统计该年份的案件
        qcount_zcs = len(cases)
        qcount_plaintiff = sum(1 for case in cases if company in case["原告"])
        qcount_defendant = sum(1 for case in cases if company in case["被告"])
        qtotal_amount = sum(float(case["涉案金额"]) for case in cases)
        qamount_plaintiff = sum(float(case["涉案金额"]) for case in cases if company in case["原告"])
        qamount_defendant = sum(float(case["涉案金额"]) for case in cases if company in case["被告"])

        count_zcs = sum(1 for case in cases if year in case["案号"])
        count_plaintiff = sum(1 for case in cases if company in case["原告"] and year in case["案号"])
        count_defendant = sum(1 for case in cases if company in case["被告"] and year in case["案号"])
        total_amount = sum(float(case["涉案金额"]) for case in cases if year in case["案号"])
        amount_plaintiff = sum(
            float(case["涉案金额"]) for case in cases if company in case["原告"] and year in case["案号"]
        )
        amount_defendant = sum(
            float(case["涉案金额"]) for case in cases if company in case["被告"] and year in case["案号"]
        )

    # 根据year是否为None来构建字典
    d = {
        f"{company}涉案次数(次)": f"{qcount_zcs}次",
        f"{company}原告涉案次数(次)": f"{qcount_plaintiff}次",
        f"{company}被告涉案次数(次)": f"{qcount_defendant}次",
        f"{company}涉案总金额(元)": f"{int(qtotal_amount)}元, {qtotal_amount:.2f}元",
        f"{company}原告涉案金额(元)": f"{int(qamount_plaintiff)}元, {qamount_plaintiff:.2f}元",
        f"{company}被告涉案金额(元)": f"{int(qamount_defendant)}元, {qamount_defendant:.2f}元",
    }

    # 如果year不是None，则添加带指定年份的键值对
    if year is not None:
        d.update(
            {
                f"{company}指定年份涉案次数(次)": f"{count_zcs}次",
                f"{company}指定年份原告涉案次数(次)": f"{count_plaintiff}次",
                f"{company}指定年份被告涉案次数(次)": f"{count_defendant}次",
                f"{company}指定年份涉案总金额(元)": f"{int(total_amount)}元, {total_amount:.2f}元",
                f"{company}指定年份原告涉案金额(元)": f"{int(amount_plaintiff)}元, {amount_plaintiff:.2f}元",
                f"{company}指定年份被告涉案金额(元)": f"{int(amount_defendant)}元, {amount_defendant:.2f}元",
            }
        )
    return d


# print(get_cishu('上汽通用五菱汽车股份有限公司'))
def func8(company_name: str):
    # 重新计算控股比例超过50%的子公司数量
    companies = get_sub_company_info_list(company_name)
    # print(companies)
    zigongsi_count = len(companies)
    # controlled_companies_count = sum(
    #  1 for company in companies
    #  if company.get('上市公司参股比例') is not None and float(company['上市公司参股比例']) == 100.0
    # )
    # controlled_companies_count
    # print(controlled_companies_count)
    # 计算投资总额，跳过投资金额为空的记录
    total_investment = sum(convert_investment_to_float(company["上市公司投资金额"]) for company in companies)

    # 准备返回的字典，包含子公司数量和投资总额
    result = {"子公司数量": f"{zigongsi_count}家", "投资总额": f"{total_investment}元"}
    result = {"子公司数量": f"{zigongsi_count}家", "子公司投资总额": f"{total_investment}元"}
    # shuliang={'子公司数量':f'{controlled_companies_count}家'}
    return result


# print(func8('中山华利实业集团股份有限公司'))
# print(get_sub_company_info_list('中山华利实业集团股份有限公司'))
def function_11(company, role="both", year=None, amount_range=None, cause=None, phase=None):
    """
    分析案件列表，根据公司作为原告或被告的角色、案件原因以及其他给定条件，汇总涉案金额和次数，并返回符合条件的案号。

    :param cases: 包含案件详情的列表
    :param target_company: 特定公司的名称，用于筛选原告或被告
    :param role: 查询角色，可选值为'defendant'（被告）、'plaintiff'（原告）或'both'（两者皆可），默认为'both'
    :param year: 指定筛选的年份，如2021
    :param amount_range: 指定的金额区间，如(0, 10000)
    :param cause: 特定的案由，如'劳务纠纷'、'合同纠纷'等
    :return: 符合条件的案号列表，以及汇总信息字典（包含'总金额'和'次数'）
    """
    company = company_name_glm4.standardize_company_name(company)
    phase_translation = {
        "民事初审": "民初",
        "民事终身": "民终",
        "执行保全财政": "执保",
        "执行": "执",
    }

    # 如果指定了阶段，进行阶段转换
    if phase:
        phase = phase_translation.get(phase, phase)

    filtered_cases = []
    total_amount = 0
    count = 0
    cases = get_legal_document_list(company)
    for case in cases:
        # 根据角色筛选条件判断是否继续处理该案件
        if role == "defendant" and company not in case["被告"]:
            continue
        elif role == "plaintiff" and company not in case["原告"]:
            continue
        elif role != "both" and (company not in case["被告"] and company not in case["原告"]):
            continue

        # 应用案由筛选
        if cause:
            if "劳务" in cause:
                if "劳务" not in case["案由"]:
                    continue
            elif "合同" in cause:
                if "合同" not in case["案由"]:
                    continue
            elif "劳动合同" in cause:
                if "劳动合同" not in case["案由"]:
                    continue
            elif "财政损害" in cause:
                if "财政损害" not in case["案由"]:
                    continue

        # 应用年份筛选
        if year and str(year) not in case["案号"]:
            continue
        if phase and phase not in case["案号"]:
            continue
        # 应用金额区间筛选
        # 处理金额区间
        # 处理金额区间
        if amount_range:
            # 如果上限是 None 或者 {}，都设置为无穷大
            if amount_range[1] is None or amount_range[1] == {}:
                adjusted_amount_upper = float("inf")
            else:
                adjusted_amount_upper = float(amount_range[1])
        else:
            adjusted_amount_upper = float("inf")
            # 金额筛选
        if amount_range:
            case_amount = float(case.get("涉案金额", 0))
            if not (amount_range[0] <= case_amount <= adjusted_amount_upper):
                continue

        # 记录符合条件的案件
        # filtered_cases.append(case['案号'])
        filtered_cases.append(
            {"案号": case["案号"], "涉案金额": case.get("涉案金额", 0), "案由": case.get("案由", "")}
        )
        # 累加金额

        total_amount += float(case.get("涉案金额", 0))
        count += 1
    total_amount_rounded = round(total_amount, 2)

    return {
        "公司名称": company,
        "涉案总金额": total_amount_rounded,
        "涉案次数": f"{count}次",
        "相关案号": filtered_cases,
    }


"""
def get_highest_legal_document_by_companyname(company_name):
    # 初始化一个变量来保存最高金额
    cases=get_legal_document_list(company_name)
    highest_amount = 0
    # 初始化一个变量来保存最高金额对应的案件
    highest_amount_case = None
    
    # 遍历每个案件
    for case in cases:
        #print(case)
        # 获取案件的涉案金额
        amount = float(case.get('涉案金额', 0))
        
        # 如果当前案件的金额高于已记录的最高金额，则更新最高金额和案件
        if amount > highest_amount:
            highest_amount = amount
            highest_amount_case = case
            
    return highest_amount_case
"""


def get_highest_legal_document_by_companyname(company_name, role=None, n=1):
    """
    获取指定公司的第 n 高或第 n 低涉案金额的法律文件信息。
    如果 n 是正数，则返回第 n 高的案件信息；
    如果 n 是负数，则返回第 |n| 低的案件信息；
    如果 n 不在有效范围内，则返回最高涉案金额的案件信息。

    :param company_name: 公司名称
    :param n: 第几高的案件（默认为 1，即最高）或第几低的案件（例如 -1 表示最低）
    :return: 字典形式的案件信息
    """
    # 获取公司相关的所有案件列表
    if role:
        if "plaintiff" in role:
            role = "原告"
        if "defendant" in role:
            role = "被告"

    cases = get_legal_document_list(company_name, role=role, need_fields=[])
    # print(cases)
    # 对案件按照涉案金额进行排序
    sorted_cases = sorted(cases, key=lambda x: float(x.get("涉案金额", 0)), reverse=True)

    # 返回第 n 高或第 |n| 低的案件信息，如果 n 不在有效范围内则返回最高案件
    if not sorted_cases:
        return None  # 如果没有案件，则返回 None

    num_cases = len(sorted_cases)

    if n >= 1:
        if 0 < n <= num_cases:
            return sorted_cases[n - 1]  # 返回第 n 高的案件
        else:
            return sorted_cases[0]  # 如果 n 大于案件数量，则返回最高案件
    elif n < 0:
        if -num_cases <= n < 0:
            return sorted_cases[num_cases + n]  # 如果 n 是负数，则返回第 |n| 低的案件
        else:
            return sorted_cases[0]  # 如果 n 小于最低有效值，则返回最高案件
    else:
        return sorted_cases[0]  # 如果 n 是 0 或其他无效值，则返回最高案件


# print( get_highest_legal_document_by_companyname('爱玛科技集团股份有限公司'))
# print(get_n_highest_or_lowest_legal_document_by_companyname('爱玛科技集团股份有限公司',n=1))
# %%

# result = function_11('山西振东医药贸易有限公司')
# print(result)
# cases=function_11('浙江晨丰科技股份有限公司',amount_range=[0.0001,{}])
# print(cases)

# cases=function_11('浙江晨丰科技股份有限公司',amount_range=[0.0001,{}])
# print(cases)


def get_top_companies_by_capital(company_name, rank_type="特定排名", rank_position=1):
    """
    根据注册资本获取顶级子公司信息。

    :param company_name: str, 母公司名称。
    :param rank_type: str, 排序类型，可选值为'最大'、'前3'或'特定排名'。
    :param rank_position: int, 当rank_type为'特定排名'时的有效参数，表示需要获取的子公司的排名位置。
    :return: list, 包含顶级子公司信息的字典列表。
    """
    s_1 = get_sub_company_info_list(company_name)
    jisu = len(s_1)
    companies = s_1
    # print(companies)
    # 过滤出含有'上市公司投资金额'且其值不为空的公司
    filtered_companies = [
        company for company in companies if "上市公司投资金额" in company and company["上市公司投资金额"] is not None
    ]

    # 对公司按照投资额排序
    filtered_companies.sort(key=lambda x: convert_investment_to_float(x["上市公司投资金额"]), reverse=True)

    # 根据rank_type和rank_position决定返回哪些公司
    if rank_type == "最高":
        top_companies = filtered_companies[:1]
    elif rank_type == "前3":
        top_companies = filtered_companies[:3]
    elif rank_type == "特定排名":
        # 处理负数的rank_position
        if rank_position < 0:
            if abs(rank_position) <= len(filtered_companies):
                top_companies = [filtered_companies[rank_position]]  # 负数索引直接使用
            else:
                raise ValueError("Invalid rank_position. It should be within the range of -len(companies) to -1.")
        else:
            if 1 <= rank_position <= len(filtered_companies):
                top_companies = [filtered_companies[rank_position - 1]]  # 用户通常从1开始计排名，因此减1
            else:
                raise ValueError("Invalid rank_position. It should be within the range of 1 to len(companies).")
    else:
        raise ValueError("Invalid rank_type.")

    # 准备输出信息
    output_keys = {
        "最高": ["投资金额最高的子公司(公司名称)", "最高投资金额", "与上市公司的关系", "总子公司数量"],
        "前3": ["前三投资额子公司名称", "投资金额", "上市公司联系", "子公司总量"],
        "特定排名": [f"特定排名第{rank_position}高子公司名称", "投资金额", "上市公司关联", "总子公司数"],
    }

    # 确保rank_type存在对应的keys
    if rank_type not in output_keys:
        raise ValueError("Invalid rank_type.")

    # 使用相应的键构建返回信息
    top_companies_info = [
        {
            output_keys[rank_type][0]: company["公司名称"],
            output_keys[rank_type][1]: company["上市公司投资金额"],
            # output_keys[rank_type][2]: company['上市公司关系'],
            # output_keys[rank_type][3]: jisu
        }
        for company in top_companies
    ]

    return top_companies_info


# print(get_top_companies_by_capital(company_name='安徽皖仪科技股份有限公司', rank_type='最高', rank_position=1))


# 调用glm4模型
def glm4_create(max_attempts, messages, tools):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="GLM-4-plus",  # 填写需要调用的模型名称#GLM-4
            messages=messages,
            tools=tools,
        )
        print(attempt)
        if response.choices and response.choices[0].message and response.choices[0].message.content:

            if '```python' in response.choices[0].message.content:
                # 如果结果包含字符串'python'，则继续下一次循环
                continue
            else:
                # 一旦结果不包含字符串'python'，则停止尝试
                break
        else:
             return response
    # 检查最终的response是否仍然包含字符串'python'
    # if 'python' in response.choices[0].message.content:
    #  raise ValueError("最终响应中仍然包含字符串'python'")
    # 返回最终的response
    return response


# 执行函数部分
def get_answer_2(question, tools, api_look: bool = True):
    if api_look:
        _, api_list_filter, filtered_tools = API_look1.API_look(question, tools)
        print(api_list_filter)
        print(filtered_tools)
        # print(filtered_tools)
    else:
        filtered_tools = tools
    try:
        function_result_logger = []
        ques = question
        # ques=pre_question.pre_que1(ques)
        messages = []

        messages.append(
            {
                "role": "system",
                "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分",
            }
        )
        # messages.append({"role": "system", "content": "你是一个工具调用执行助手，你要根据用户给你指令区调用function,如果用户提到api其实就是让你调用function。要根据工具调用结果回答问题自己不要总结。不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分。"})

        messages.append({"role": "user", "content": ques})

        response = glm4_create(10, messages, filtered_tools)
        print(response.choices[0].message)
        messages.append(response.choices[0].message.model_dump())
        messages1 = []

        # messages1.append({"role": "system", "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息,要区分"})
        messages1.append({"role": "user", "content": ques})

        jisu = 1
        max_iterations = 5  # 设置一个最大循环次数限制
        print("-----------123--------------")
        while response.choices[0].message.tool_calls and jisu <= max_iterations:
            tool_call = response.choices[0].message.tool_calls[0]
            args = tool_call.function.arguments
            print("------------------args-----------------")
            print(args)

            function_result = {}
            """
            function_names = [tool["function"]["name"] for tool in tools]

            # Creating the function_map dictionary
            function_map = {name: name for name in function_names}
                        
            print(function_map)
            """
            function_map = {
                "get_company_info": get_company_info,
                "get_company_register": get_company_register,
                "get_company_register_name": get_company_register_name,
                "get_sub_company_info": get_sub_company_info,
                "get_sub_company_info_list": get_sub_company_info_list,
                "get_legal_document": get_legal_document,
                "get_legal_document_list": get_legal_document_list,
                "get_court_info": get_court_info,
                "get_court_code": get_court_code,
                # 'get_lawfirm_info': get_lawfirm_info,
                # 'get_lawfirm_log': get_lawfirm_log,
                "get_lawfirm_info_log": get_lawfirm_info_log,
                "get_address_info": get_address_info,
                "get_address_code": get_address_code,
                "get_temp_info": get_temp_info,
                "get_legal_abstract": get_legal_abstract,
                "get_xzgxf_info": get_xzgxf_info,
                "get_xzgxf_info_list": get_xzgxf_info_list,
                "check_company": check_company,
                "func8": func8,
                "function_11": function_11,
                "get_top_companies_by_capital": get_top_companies_by_capital,
                "check_restriction_and_max_amount": check_restriction_and_max_amount,
                "calculate_total_amount_and_count_simple": calculate_total_amount_and_count_simple,
                "get_highest_legal_document_by_companyname": get_highest_legal_document_by_companyname,
            }

            function_name = tool_call.function.name
            function = function_map.get(function_name)

            if function:
                function_result = function(**json.loads(args))
            # else:
            #    raise ValueError(f"Unknown function: {function_name}")

            print(f"--------第{jisu}次---接口调用查询返回结果---------{function_result}")
            function_result_logger.append(function_result)
            messages1.append({"role": "tool", "content": f"{function_result}", "tool_call_id": tool_call.id})
            try:
                print(messages1)
                response = glm4_create(12, messages1, filtered_tools)
                print(response.choices[0].message.content)
            except Exception as e:
                print(f"API调用出错：{e}")
                break
            print(response.choices[0].message)
            jisu += 1

        if jisu > max_iterations:
            print("达到最大循环次数，退出循环")

        return response.choices[0].message.content, function_result_logger

    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None, None


def merged_dicts(dicts):
    # 初始化一个空字典用于存储合并后的结果
    merged_dict = {}

    # 检查dicts是否是列表类型
    if not isinstance(dicts, list):
        print("传入的参数不是列表类型，无法合并。")
        return merged_dict  # 或者可以选择抛出异常: raise ValueError("参数必须是一个字典列表")

    # 遍历列表中的每个字典，并使用update方法合并
    for d in dicts:
        merged_dict.update(d)

    # 输出合并后的字典
    print(merged_dict)
    return merged_dict


def get_answer_2_2(ques, API_log):
    answer, function_result_logger = get_answer_2(ques)
    answer_a = answer  # answer+str(function_result_logger)
    answer_api = API_diaoyong.API_count_agent(ques, answer_a, API_log)
    print("--------------答案如下------------------")
    return answer_api


def extract_values(data):
    values = []
    if isinstance(data, dict):
        for key in data:
            values.extend(extract_values(data[key]))
    elif isinstance(data, list):
        for item in data:
            values.extend(extract_values(item))
    else:
        values.append(data)
    return values


def answer_yh(question, answer, function_result_logger):
    if "摘要" in question:
        answer_yh = str(function_result_logger)
        return answer_yh
    else:
        LL = extract_values(function_result_logger)
        if LL:
            LL2 = [i for i in LL if str(i) not in answer]

        if LL2:
            if len(str(set(LL2))) < 10 * len(answer):
                answer_yh = answer + str(set(LL2))
            else:
                answer_yh = answer
        else:
            answer_yh = answer

        return answer_yh
if __name__ == "__main__":
    print(get_highest_legal_document_by_companyname('重庆啤酒股份有限公司',n=2))