import json
from typing import List, Union
from apis.data_query_api import *
import re
from tools.tools_register import * 
from typing import get_origin, Annotated, Union, List, Optional
from utils import convert_to_float, parse_json_to_df
import pandas as pd 
from pandas import DataFrame
from llm.glm_llm import call_glm4
from datetime import datetime
import numpy as np 
def keywords_parser(response: str) -> list:
    # print(response.content)
    if isinstance(response, dict):
        return response['Items']
    
    if isinstance(response, list):
        return response
    # print(response)
    pattern = r"\[(.*?)\]"
    matches = re.search(pattern, response.replace("\n", ""))
    if matches:
        # print(response)
        list_content = matches.group(1)
        # 将字符串转换为列表
        result_list = [item.strip("\'").strip() for item in list_content.split(",")]
    elif "," in response:
        result_list = [item.strip("\'").strip() for item in response.split(",")]
    else :
        result_list =  [response]
    return result_list


def extract_fees(row):
    # print(row)
    text = row["判决结果"] 
    # print(text)
    # 正则表达式匹配受理费用
    match = re.search(r'案件受理费(\d+)元', text)
    if match:
        total_fee = match.group(1)
        return convert_to_float(total_fee)
    else:
        return 0

@register_tool
def get_listed_company_info_service(company_name:  Annotated[str, "公司名称", True]) -> DataFrame:
    """
    (优先使用)根据上市公司名称，获得该上市公司对应的基本信息, 包括公司代码(股票代码),主营业务,法人代表等 (常用),，可以用他来判断是否为上市公司,返回为空不为上市公司。
    若上市公司查询不到信息如注册地址，办公地址等，请使用get_company_register_service.
    强烈注意: 本工具不能查询公司的注册资本，注册资本查询请使用get_company_register_service.
    参数:
    company_name -- 公司名称，例如: 上海妙可蓝多食品科技股份有限公司 注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。

    返回结果数量: 1条
    返回字段名称： ['公司名称', '公司简称', '英文名称', '关联证券', '公司代码', '曾用简称', '所属市场', '所属行业', '成立日期', '上市日期', '法人代表', '总经理’' '董秘’,''邮政编码', '注册地址', '办公地址', '联系电话', '传真’,''官方网址', '电子邮箱', '入选指数', '主营业务', '经营范围', '机构简介', '每股面值', '首发价格', '首发募资净额', '首发主承商']
    """
    rsp = get_company_info(query_conds={"公司名称": company_name}, need_fields=[])
    df = parse_json_to_df(rsp)
    if df.shape[0] == 0:
        return df
    df['首发募资净额'] = df['首发募资净额'].apply(convert_to_float) * 10000
    return df 


#公司简称查：根据公司简称查
@register_tool
def get_company_info_service_by_abbreviation(company_abbreviation:  Annotated[str, "公司简称", True])-> DataFrame:
    """
   	根据公司简称，获得该公司对应的公司全称。
    
    参数:
    company_abbreviation -- 公司简称，例如: 百度，腾讯等等较短且不带'公司'二字的实体

    返回结果数量：1条
    返回字段名称：['公司简称','公司名称']
    """
    rsp = get_company_info(query_conds={"公司简称": company_abbreviation},need_fields=[])
    if rsp == []:
        return DataFrame()
    else:
        company_name = rsp['公司名称']
    df = DataFrame([[company_abbreviation, company_name]], columns=['公司简称','公司名称'])
    return df

#公司代码查：根据公司代码查
@register_tool
def get_company_info_service_by_code(company_code:  Annotated[str, "公司代码", True]) -> DataFrame:
    """
   	根据公司代码(公司股票代码)，获得该公司对应的公司全称 公司代码6位或者7位
    参数:
    company_code -- 公司代码，例如: 300682

    返回结果数量：1条
    返回字段名称：['公司代码','公司名称']。
    """
    # need_fields = keywords_parser(need_fields)
    if len(company_code) == 12:
        company_code = company_code[::2]
                
    rsp = get_company_info(query_conds={"公司代码": company_code},need_fields=[])
    if rsp == []:
        return DataFrame()
    else:
        company_name = rsp['公司名称']
    
    # json_str = json.dumps(rsp, ensure_ascii=False)
    df = DataFrame([[company_code, company_name]], columns=['公司代码','公司名称'])
    return df 

@register_tool
def get_company_register_service(company_name: Annotated[str, "公司名称", True]) -> DataFrame:
    """
    本工具查询公司的工商信息，注册资本请使用本工具查, 子母公司查询时常用来补充注册资本等信息。
    
    company_name -- 公司名称，例如"上海妙可蓝多食品科技股份有限公司" 注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。


    返回结果数量：1条
    返回字段名称：['公司名称', '登记状态', '统一社会信用代码', '法定代表人', '注册资本', '成立日期', '企业地址', '联系电话', '联系邮箱', '注册号', '组织机构代码', '参保人数', '行业一级', '行业二级', '行业三级', '曾用名', '企业简介', '经营范围']。

    """
    rsp = get_company_register(query_conds={"公司名称": company_name},need_fields=[])
    df = parse_json_to_df(rsp)
    try:
        df['注册资本'] = df['注册资本'].astype(float) * 10000
    except:
        df['注册资本'] = 0
    return df


@register_tool
def get_company_name_by_uniform_social_code_service(Uniform_social_redit_code: Annotated[str, "公司的统一社会信用代码", True]= []) -> DataFrame:
    """
    根据公司的统一社会信用代码查询公司名称，统一社会信用代码为18位字符串。

    参数:
    Uniform_social_redit_code -- 统一社会信用代码，例如： 913305007490121183

    返回结果数量：1条
    返回字段名称：['统一社会信用代码','公司名称']。

    """
    rsp = get_company_register_name(query_conds={"统一社会信用代码": Uniform_social_redit_code})
    if rsp == []:
        return DataFrame()
    else:
        company_name = rsp['公司名称']
    # print(rsp)
    # 
    # json_str = json.dumps(rsp, ensure_ascii=False)
    df = DataFrame([[Uniform_social_redit_code, company_name]], columns=['统一社会信用代码','公司名称'])

    return df

@register_tool
def get_parent_company_info_by_child_company_name_service(sub_company_name: Annotated[str, "子公司全称", True]) -> DataFrame:
    """
    根据被投资的子公司名称获得投资该公司的母公司名称、投资比例、投资金额等信息。

    参数:
    sub_company_name -- 被投资的子公司全称，例如: 上海爱斯达克汽车空调系统有限公司 注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。

    返回结果数量：1条
    返回字段名称：['母公司全称', '母公司参股比例', '母公司投资金额', '子公司名称']。
    """ 
    rsp = get_sub_company_info(query_conds={"公司名称": sub_company_name},need_fields=[])
    ### 修改字段
    if '关联上市公司全称' in rsp:
        rsp['母公司全称'] = rsp.get('关联上市公司全称', "")
        del rsp['关联上市公司全称']
    if '上市公司关系' in rsp:
        rsp['母公司关系'] = rsp.get('上市公司关系', "")
        del rsp['上市公司关系']
    if '上市公司参股比例' in rsp:
        rsp['母公司参股比例'] = convert_to_float(rsp.get('上市公司参股比例',"0"))
        del rsp['上市公司参股比例']
    if '上市公司投资金额' in rsp:
        rsp['母公司投资金额'] = convert_to_float(rsp.get('上市公司投资金额', "0万"))
        del rsp['上市公司投资金额']        
    if '公司名称' in rsp:
        rsp['子公司名称'] = rsp.get('公司名称',"")
        del rsp['公司名称']
        
    df = parse_json_to_df(rsp)
    return df 

#子公司查询：1、投资金额进行筛选，下界 2、做好排序，从小到大 3、增加一共有多少家，输出子公司数量（家）
@register_tool
def get_listed_sub_company_info_service_by_parent_company_name(parent_company_name: Annotated[str, "母公司全称", True]) -> DataFrame:
    """
    根据母公司的名称查询该公司投资的所有子公司信息列表, 注意要查子公司的基本信息或者注册信息，请接着结合get_listed_company_info_service, get_registered_company_info_service使用。

    当涉及整个成报告问题时，请把need_fields传入空列表[],表示返回全部字段。
    参数:
    parent_company_name -- 母公司全称，例如"天能电池集团股份有限公司" 注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。

    返回结果数量：多条
    返回字段名称：['母公司全称', '母公司关系', '母公司参股比例', '母公司投资金额', '子公司名称']
    """

    rsp = get_listed_sub_company_info(query_conds={"关联上市公司全称": parent_company_name},need_fields=[])
    new_list = []
    if isinstance(rsp, dict):
        rsp = [rsp]
    for item in rsp:
        if '关联上市公司全称' in item:
            item['母公司全称'] = item.get('关联上市公司全称', "")
            del item['关联上市公司全称']
        if '上市公司关系' in item:
            item['母公司关系'] = item.get('上市公司关系', "")
            del item['上市公司关系']
        if '上市公司参股比例' in item:
            item['母公司参股比例'] = convert_to_float(item.get('上市公司参股比例',"0"))
            del item['上市公司参股比例']
        if '上市公司投资金额' in item:
            item['母公司投资金额'] =convert_to_float(item.get('上市公司投资金额', "0万")) 
            del item['上市公司投资金额']        
        if '公司名称' in item:
            item['子公司名称'] = item.get('公司名称',"")
            del item['公司名称']
        new_list.append(item) 
    new_list = sorted(new_list, key=lambda x: float(x["母公司参股比例"]), reverse=False)
   
    return parse_json_to_df(new_list)


#全资子公司查询：1、投资金额进行筛选，下界 2、做好排序，从小到大 3、增加一共有多少家，输出子公司数量（家）
@register_tool
def get_listed_all_sub_company_info_service_by_parent_company_name(parent_company_name: Annotated[str, "母公司全称", True]) -> DataFrame:
    """
    根据母公司的名称查询该公司投资的所有全资子公司信息列表，注意要查子公司的基本信息或者注册信息，请接着结合get_listed_company_info_service, get_registered_company_info_service使用。

    当涉及整个成报告问题时，请把need_fields传入空列表[],表示返回全部字段。
    参数:
    parent_company_name -- 母公司全称，例如"天能电池集团股份有限公司" 注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。

    返回结果数量：多条
    返回字段名称：['母公司全称', '母公司关系', '母公司参股比例', '母公司投资金额', '全资子公司名称']
    """

    rsp = get_listed_sub_company_info(query_conds={"关联上市公司全称": parent_company_name},need_fields=[])
    new_list = []
    if isinstance(rsp, dict):
        rsp = [rsp]
    for item in rsp:
        if '关联上市公司全称' in item:
            item['母公司全称'] = item.get('关联上市公司全称', "")
            del item['关联上市公司全称']
        if '上市公司关系' in item:
            item['母公司关系'] = item.get('上市公司关系', "")
            del item['上市公司关系']
        if '上市公司参股比例' in item:
            item['母公司参股比例'] = convert_to_float(item.get('上市公司参股比例',"0"))
            del item['上市公司参股比例']
        if '上市公司投资金额' in item:
            item['母公司投资金额'] =convert_to_float(item.get('上市公司投资金额', "0万")) 
            del item['上市公司投资金额']        
        if '公司名称' in item:
            item['全资子公司名称'] = item.get('公司名称',"")
            del item['公司名称']
        if  item["母公司参股比例"] == 100 :
            new_list.append(item) 
    
    new_list = sorted(new_list, key=lambda x: float(x["母公司参股比例"]), reverse=False)
   
    return parse_json_to_df(new_list)

@register_tool
def get_legal_document_service(reference: Annotated[str, "案号", True]) -> DataFrame:
    """
    根据案号查询该案件的裁判文书相关信息，要查询案件的审理法院信息可以使用get_court_name_service_by_reference获取法院名称后再利用get_court_info_service获取法院信息.
    同理要查询案件的被告，原告信息请使用get_listed_company_service_by_reference获取上市公司信息或者使用get_company_info_service获取公司信息.
    同理要查询案件的被告律师事务所，原告律师事务所信息请使用get_law_firm_info_service获取律师事务所信息.


    参数:
    reference -- 案号，例如: (2019)沪0115民初61975号

    返回结果数量：1条
    返回字段名称：['关联公司', '标题', '案号', '年份', '文书类型', '原告', '被告', '原告律师事务所', '被告律师事务所', '案由','受理费','涉案金额', '判决结果', '日期', '文件名'] 
    """           
    reference = reference.replace('（', '(').replace('）', ')')
    
    rsp = get_legal_document(query_conds={"案号": reference},need_fields=[])
    if rsp == []:
        #英文文半角括号转中文
        reference = reference.replace('(', '（').replace(')', '）')
        rsp = get_legal_document(query_conds={"案号": reference},need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    df = parse_json_to_df(rsp)
    if df.shape[0] == 0:
        return df
    try:
        df['受理费'] = df.apply(extract_fees, axis=1)
    except:
        df['受理费'] = 0
    df['年份'] = df['案号'].apply(lambda x: x[1:5])
    df['涉案金额'] = df['涉案金额'].apply(lambda x: convert_to_float(x))
    return df


#涉案金额：根据公司名称查涉案金额：1、涉案金额设置上界和下界 2、筛选年份，固定某一年 3、排序，从小到大 4、输出案件数量
@register_tool
def get_company_involved_cases_info_service(company_name: Annotated[str, "涉案公司", True], need_fields: Annotated[list, "需要返回的字段列表 ['关联公司', '标题', '案号', '文书类型', '原告', '被告', '原告律师事务所', '被告律师事务所', '案由', '涉案金额', '判决结果', '日期', '文件名']", True]= []) -> DataFrame:
    
    """
    根据关联涉案公司和筛选条件查询它所有的涉及案件信息。
    根据案号查询该案件的裁判文书相关信息，要查询案件的审理法院信息可以使用get_court_name_service_by_reference获取法院名称后再利用get_court_info_service获取法院信息.
    同理要查询案件的被告，原告信息请使用get_listed_company_service_by_reference获取上市公司信息或者使用get_company_info_service获取公司信息.
    同理要查询案件的被告律师事务所，原告律师事务所信息请使用get_law_firm_info_service获取律师事务所信息.

    当涉及整个成报告问题时，请把need_fields传入空列表[],表示返回全部字段。
    当要筛选民事初审案件时，案件所对应的标题应该含有"一审民事"字样，,请自行筛选 ，其他同理筛选格式为X审(诉讼类型)。
    当要筛选原告/被告是XX的案件时，请注意不要使用等于，而是使用包含，即使用.contains(XX)函数，请自行筛选。

    参数:
    company_name -- 关联涉案公司，例如"上海爱斯达克汽车空调系统有限公司"  注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。
    need_fields -- 需要返回的字段列表，仅接受空列表[]或者其他字段列表例如[关联公司, 案号,原告,被告,原告律师事务所,被告律师事务所,案由,涉案金额,日期],need_fields传入空，则表示返回所有字段，否则返回填入的字段
    
    返回结果数量：多条
    返回字段名称：['关联公司', '标题', '案号', '年份', '文书类型', '原告', '被告', '原告律师事务所', '被告律师事务所', '案由', '受理费', '涉案金额', '判决结果', '日期', '文件名']
    
    """

    if '年份' in need_fields and need_fields != []:
        if '年份' in need_fields:
            need_fields.remove('年份')
        if  '案号' not in need_fields:
            need_fields.append('案号')
    
    if '受理费' in need_fields:
        need_fields.remove('受理费')
        if  '判决结果' not in need_fields:
            need_fields.append('判决结果')
    rsp = get_legal_document_list(query_conds={"关联公司": company_name},need_fields=need_fields)
    

    if isinstance(rsp, dict):
        rsp = [rsp]
    df = parse_json_to_df(rsp)
    if df.shape[0] == 0:
        return df 

    if '判决结果' in df.columns:
        try:
            df['受理费'] = df.apply(extract_fees, axis=1)
        except:
            df['受理费'] = 0
    
    if '涉案金额' in df.columns:
        df['涉案金额'] = df['涉案金额'].apply(lambda x: convert_to_float(x))
    
    if '案号' in df.columns or need_fields == []:
        df['年份'] = df['案号'].apply(lambda x: x[1:5])
    print(df.columns)
    return df


@register_tool
def get_court_info_service(court_name: Annotated[str, "法院名称", True]) -> DataFrame:
    """
    根据法院名称查询法院地理位置和负责人等相关信息。
    
    参数:
    court_name -- 法院名称，例如"上海市浦东新区人民法院", 不允许输入法院代号

    返回结果数量：1条
    返回字段名称：['法院名称', '法院负责人', '成立日期', '法院地址', '法院联系电话', '法院官网']
    """
    #print("输出结果：",need_fields)
    rsp = get_court_info(query_conds={"法院名称": court_name},need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return parse_json_to_df(rsp)



@register_tool
def get_court_code_service(court_name: Annotated[str, "法院名称\法院代字", True]) -> DataFrame:
    """
    根据法院名称或者法院代字查询法院级别和代号等相关数据。
    案号规范：(收案年度) ＋ 法院代字＋ 类型代字＋案件编号＋“号”如：(2024)京01民再36号
    
    参数:
    court_name -- 法院名称或者法院代字，例如"上海市浦东新区人民法院"或者"沪0115"

    返回结果数量：1条
    返回字段名称：['法院名称', '行政级别', '法院级别', '法院代字', '区划代码', '级别']
    """
    if "法院" in court_name:
        rsp = get_court_code(query_conds={"法院名称": court_name},need_fields=[])
    else:
        rsp = get_court_code(query_conds={"法院代字": court_name},need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return parse_json_to_df(rsp)


@register_tool
def get_lawfirm_info_service(law_firm_name: Annotated[str, "律师事务所名称", True] ) -> DataFrame:
    """
    根据律师事务所名称查询律师事务所人事，地理位置，注册金额等信息。
    参数:
    law_firm_name -- 律师事务所名称，例如"北京市金杜律师事务所"

    返回结果数量：1条
    返回字段名称：['律师事务所名称', '律师事务所唯一编码', '律师事务所负责人', '事务所注册资本', '律师事务所成立日期', '律师事务所地址', '通讯电话', '通讯邮箱', '律所登记机关']
    """
    rsp = get_lawfirm_info(query_conds={"律师事务所名称": law_firm_name},need_fields=[])
    df = parse_json_to_df(rsp)
    if df.shape[0] == 0:
        return df
    if '事务所注册资本' in df.columns:
        df['事务所注册资本'] = df['事务所注册资本'].apply(lambda x: convert_to_float(x.strip("元人民币").strip("人民币")))
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return df

@register_tool
def get_lawfirm_business_service(law_firm_name: Annotated[str, "律师事务所名称", True] ) -> DataFrame:
    """
    根据律师事务所名称查询律师事务所业务情况统计数据。

    参数:
    law_firm_name -- 律师事务所名称，例如"北京市金杜律师事务所"

    返回结果数量：1条
    返回字段名称：['律师事务所名称', '业务量排名', '服务已上市公司', '报告期间所服务上市公司违规事件', '报告期所服务上市公司接受立案调查']
    """
    rsp = get_lawfirm_log(query_conds={"律师事务所名称": law_firm_name},need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return parse_json_to_df(rsp)

@register_tool
def get_address_info_service(address: Annotated[str, "地址", True]) -> DataFrame:
    """
    根据地址查该地址对应的省份城市区县，地址信息仅接受精确到街道房屋号等信息如 上海市浦东新区丁香路611号 ，不接受公司名称，不接受法院名称，不接受律所名称等模糊查询。

    参数:
    address -- 地址，例如"西藏自治区那曲地区安多县帕那镇中路13号"

    返回结果数量：1条
    返回字段名称：['地址', '省份', '城市', '区县']
    """

    rsp = get_address_info(query_conds={"地址": address},need_fields=[])
    return parse_json_to_df(rsp)

@register_tool
def get_address_code_service(province: Annotated[str, "省份", True],city: Annotated[str, "城市", True],county: Annotated[str, "区县", True] ) -> DataFrame:
    """
    根据省市区查询区划代码，注意省份，城市，区县必须全部输入,注意若是直辖市则省份城市都需要传入直辖市名称。

    参数:
    province -- 省份，例如"西藏自治区"
    city -- 城市，例如"拉萨市"
    county -- 区县，例如"城关区"

    返回结果数量：1条
    返回字段名称：['省份', '城市', '城市区划代码', '区县', '区县区划代码']
    """
    rsp = get_address_code(query_conds={"省份": province, "城市": city, "区县": county},need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return parse_json_to_df(rsp)

@register_tool
def get_temp_info_service(province: Annotated[str, "省份", True],city: Annotated[str, "城市", True],date: Annotated[str, "日期", True] ) -> DataFrame:
    """
    根据日期及省份城市查询天气相关信息，注意若是直辖市则省份城市都需要传入直辖市名称，仅接受日期格式为YYYY年MM月DD日 如：2020年1月23日]，注意日为10以下无需加0如 2024年8月5日。
    日期可通过如下函数完成转换环境内置函数format_date(直接调用)完成:
    date = format_date("2020-11-06 00:00:00") 
    即: 2020-11-06 00:00:00 --> 2020年11月6日
    2020年11月6日
    
    参数:
    province -- 省份，例如"北京市"
    city -- 城市，例如"北京市"
    date -- 日期，例如"2020年1月1日"

    返回结果数量：1条
    返回字段名称：['日期', '省份', '城市', '天气', '最高温度', '最低温度', '湿度']
    """
    rsp = get_temp_info(query_conds={"省份": province, "城市": city, "日期": date}, need_fields=[])
    # json_str = json.dumps(rsp, ensure_ascii=False)
    return parse_json_to_df(rsp)

@register_tool
def get_legal_abstract_by_reference_service(reference: Annotated[str, "案号", True]) -> DataFrame:
    """
    根据案号查询文本摘要，返回内容：['文件名', '案号', '文本摘要']。

    参数:
    reference -- 案号，例如"（2019）沪0115民初61975号"

    返回结果数量：1条
    返回字段名称：['文件名', '案号', '文本摘要']
    """
    reference = reference.replace('（', '(').replace('）', ')')
    
    rsp = get_legal_abstract(query_conds={"案号": reference},need_fields=[])
    if rsp == []:
        #英文文半角括号转中文
        reference = reference.replace('(', '（').replace(')', '）')
        rsp = get_legal_abstract(query_conds={"案号": reference},need_fields=[])
    return parse_json_to_df(rsp)

@register_tool
def get_xzgxf_info_by_reference_service(reference: Annotated[str, "案号", True] ) -> DataFrame:
    """
    根据案号查询限制高消费案件相关信息。

    参数:
    reference -- 案号，例如"（2018）鲁0403执1281号"

    返回结果数量：1条
    返回字段名称：['限制高消费企业名称', '案号', '法定代表人', '申请人', '涉案金额', '执行法院', '立案日期', '限高发布日期']
    """ 
    reference = reference.replace('（', '(').replace('）', ')')
    # print(reference)

    
    rsp = get_xzgxf_info(query_conds={"案号": reference},need_fields=[])
    if rsp == []:
        #英文文半角括号转中文
        reference = reference.replace('(', '（').replace(')', '）')
        rsp = get_xzgxf_info(query_conds={"案号": reference},need_fields=[])

    df = parse_json_to_df(rsp)
    if df.shape[0] ==0:
        return df 
    df['涉案金额'] = df['涉案金额'].apply(lambda x: convert_to_float(x))
    return parse_json_to_df(rsp)

#限制高消费：根据公司名称查涉限制高消费
@register_tool
def get_company_xzgxf_by_company_name_service(company_name: Annotated[str, "涉案公司", True], need_fields: Annotated[list, "需要返回的字段列表 [限制高消费企业名称,案号,法定代表人,申请人,涉案金额,执行法院,立案日期,限高发布日期]", True]= []) -> DataFrame:
    """
    根据公司名称查询它所有涉及限制高消费案件相关信息，返回内容。
    注意：每调用一次该函数，返回的结果一定要保存, 当涉及整个成报告问题时，请把need_fields传入空列表[],表示返回全部字段。

    参数:
    company_name -- 公司名称，例如"欣水源生态环境科技有限公司"  注意:仅仅接收公司全称，不接受公司代码，统一社会信用代码。
    need_fields -- 需要返回的字段列表，仅接受空列表[]或者其他字段列表 例如[限制高消费企业名称,案号,法定代表人,申请人,涉案金额, 立案日期],need_fields传入，则表示返回所有字段，否则返回填入的字段
    
    返回结果数量：多条
    返回字段名称：['限制高消费企业名称', '年份', '案号', '法定代表人', '申请人', '涉案金额', '执行法院', '立案日期', '限高发布日期']
    """
    
    raw_need_fields = need_fields.copy()
    if '年份' in need_fields or need_fields != []:
        if '年份' in need_fields:
            need_fields.remove('年份')
        if '案号' not in need_fields:
            need_fields.append('案号')
    

    rsp = get_xzgxf_info_list(query_conds={"限制高消费企业名称": company_name}, need_fields=need_fields)
    if isinstance(rsp, dict):
        rsp = [rsp]
    df = parse_json_to_df(rsp)
    if df.shape[0] ==0:
        return df 
    if '涉案金额' in df.columns:
        df['涉案金额'] = df['涉案金额'].apply(lambda x: convert_to_float(x))

    if '案号' in df.columns or need_fields == []:
        df['年份'] = df['案号'].apply(lambda x: x[1:5])

    return df
   

#根据案号返回法院名称
@register_tool
def get_court_name_service_by_reference(reference: Annotated[str, "案号", True]) -> DataFrame:
    """
    根据案号返回审理法院名称。

    参数:
    reference -- 案号 例如: 

    返回结果数量：1
    返回字段名称：['案号','审理法院名称']
    """
    reference = reference.replace('（', '(').replace('）', ')')
    pattern = re.compile(r'[\u4e00-\u9fa5](\d+)')
    match = pattern.search(reference)
    result = match.group(0) if match else None
    court_name = get_court_code_service(court_name=result)["法院名称"][0]
    df = DataFrame([[reference, court_name]], columns=['案号','审理法院名称'])

    return df


### 民事起诉状(生成默认字典)
def generate_sue_info_default_dict(plaintiff_type, defendant_type):
    def get_person_fields(prefix):
        return {
            f'{prefix}': '',
            f'{prefix}性别': '',
            f'{prefix}生日': '',
            f'{prefix}民族': '',
            f'{prefix}工作单位': '',
            f'{prefix}地址': '',
            f'{prefix}联系方式': ''
        }

    def get_company_fields(prefix):
        return {
            f'{prefix}': '',
            f'{prefix}地址': '',
            f'{prefix}法定代表人': '',
            f'{prefix}联系方式': ''
        }

    default_dict = {}

    # 原告字段
    if plaintiff_type.lower() == '公民':
        default_dict.update(get_person_fields('原告'))
    elif plaintiff_type.lower() == '公司':
        default_dict.update(get_company_fields('原告'))

    # 被告字段
    if defendant_type.lower() == '公民':
        default_dict.update(get_person_fields('被告'))
    elif defendant_type.lower() == '公司':
        default_dict.update(get_company_fields('被告'))

    # 共同字段
    common_fields = {
        '原告委托诉讼代理人': '',
        '原告委托诉讼代理人联系方式': '',
        '被告委托诉讼代理人': '',
        '被告委托诉讼代理人联系方式': '',
        '诉讼请求': '',
        '事实和理由': '',
        '证据': '',
        '法院名称': '',
        '起诉日期': ''
    }
    default_dict.update(common_fields)

    return default_dict


### 民事起诉状(提取基础信息)
@register_tool
def get_sue_base_info_serivce(question: Annotated[str, "问题", True]) -> str:
    """
    根据民事起诉状的问题提取问题中提到的所有有关字段

    参数:
    question -- 问题 例如: 

    返回结果数量: 1
    返回字段名称: ['起诉状']
    """

    
    prompt = """
    你是一个专业的法律助手。你的任务是从给定的问题中提取与示例字典中存在的相关信息,并以JSON格式返回。

    示例字典中的键值对如下:
    如果原告或者被告是公民，那么其包含的字段应该有：性别、生日、民族、工作单位、地址和联系方式；
    如果原告或者被告是公司，那么其包含的字段应该有：地址、法定代表人、联系方式。

    下面是一个原告为公民，被告为公司的示例字典的例子：
    {{
        '原告身份': '', '被告身份': '',
        '原告': '', '原告性别': '', '原告生日': '', '原告民族': '', '原告工作单位': '', '原告地址': '', '原告联系方式': '',
        '原告委托诉讼代理人': '', '原告委托诉讼代理人联系方式': '',
        
        '被告': '', '被告地址': '', '被告法定代表人': '', '被告联系方式': '',
        '被告委托诉讼代理人': '', '被告委托诉讼代理人联系方式': '',

        '诉讼请求': '', '事实和理由': '', '证据': '', '法院名称': '', '起诉日期': ''
    }}

    下面是一个原告为公司，被告为公司的示例字典的例子：
    {{
        '原告身份': '', '被告身份': '',
        '原告': '', '原告地址': '', '原告法定代表人': '', '原告联系方式': '',
        '原告委托诉讼代理人': '', '原告委托诉讼代理人联系方式': '',
        
        '被告': '', '被告地址': '', '被告法定代表人': '', '被告联系方式': '',
        '被告委托诉讼代理人': '', '被告委托诉讼代理人联系方式': '',

        '诉讼请求': '', '事实和理由': '', '证据': '', '法院名称': '', '起诉日期': ''
    }}

    请仔细分析以下问题,并提取所有与上述字典中存在的键相关的信息。如果某个键在问题中没有对应的信息,请不要包含该键在输出中。
    确保返回的JSON格式正确,只包含从问题中提取的信息。

    请注意：
    1. 如果原告或者被告涉及到公司，那么请添加一个新的字段："原告公司"或"被告公司"，且如若题目没有提供姓名，在'原告'或者'被告'处填写: 公司名称+原告或者被告与公司的关系。
    2. 如果原告或者被告是普通公民，那么'原告'或者'被告'应该是他们的名字，如若题目没有提供姓名，则用'无'代替。
    3. 一定要仔细判断好原告和被告的身份，并且在原告身份和被告身份中填写'公民'或'公司'。
    4. 请注意法人并不能代表公司。涉及法人、董事或董秘等人物，统一分类为'公民'。

    下面我给你一个问题例子：

    南京康尼机电股份有限公司法人江川播与江苏江南高纤股份有限公司发生了民事纠纷，原告法人生日为1972/04/11，喜欢吃苹果，南京康尼机电股份有限公司委托给了江西辰星律师事务所，江苏江南高纤股份有限公司委托给了江西心者律师事务所，请写一份民事起诉状给青县人民法院时间是2024-02-02，注：法人的地址电话可用公司的代替。

    提取：
    {{
    '原告身份': '公民',
    '被告身份': '公司',
    '原告': '江川播',
    '原告公司': '南京康尼机电股份有限公司',
    '原告生日': '1972-04-11',
    '原告委托诉讼代理人': '江西辰星律师事务所',
    '被告': '江苏江南高纤股份有限公司',
    '原告公司': '江苏江南高纤股份有限公司',
    '被告委托诉讼代理人': '江西心者律师事务所',
    '诉讼请求': '民事纠纷',
    '事实和理由': '上诉',
    '证据': '无',
    '法院名称': '青县人民法院',
    '起诉日期': '2024-02-02'
    }}

    这是另外一个问题例子：
    南京康尼机电股份有限公司与江苏江南高纤股份有限公司的法人发生了民事纠纷，原告法人生日为1972/04/11，喜欢吃苹果，南京康尼机电股份有限公司委托给了江西辰星律师事务所，江苏江南高纤股份有限公司委托给了江西心者律师事务所，请写一份民事起诉状给青县人民法院时间是2024-02-02，注：法人的地址电话可用公司的代替。

    提取：
    {{
    '原告身份': '公司',
    '被告身份': '公民',
    '原告': '南京康尼机电股份有限公司',
    '原告公司': '南京康尼机电股份有限公司',
    '原告委托诉讼代理人': '江西辰星律师事务所',
    '被告': '江苏江南高纤股份有限公司的法人',
    '被告公司': '南京康尼机电股份有限公司',
    '被告委托诉讼代理人': '江西心者律师事务所',
    '诉讼请求': '民事纠纷',
    '事实和理由': '上诉',
    '证据': '无',
    '法院名称': '青县人民法院',
    '起诉日期': '2024-02-02'
    }}

    这是我的问题: {question}

    请以JSON格式返回提取的信息, 确保返回的JSON格式正确，只包含整合后的信息。不要返回任何额外的解释或文字，也不需要包含开头的 ```json 和结尾的 ```，而是以'{{'开头以'}}'结尾。

    请以JSON格式返回整合后的信息：
    """

    full_prompt = prompt.format(question=question)
    result = call_glm4(full_prompt)
    # print(result)

    # # 尝试解析嵌套的 JSON 字符串
    # try:
    #     # 首先解除外层的 JSON 转义
    #     base_info = json.loads(base_info)
    #     # print("After first json.loads:", type(base_info))
        
    #     # 再次解析成为字典
    #     base_info_dict = json.loads(base_info)
    #     # print("After second json.loads:", type(base_info_dict))

    #     base_info = json.dumps(base_info_dict, ensure_ascii=False, indent=2)
    #     # print("Content:", base_info)
    # except json.JSONDecodeError as e:
    #     print("JSON解析错误:", str(e))

    return result


### 民事起诉状(整合信息)
# @register_tool
def conform_sue_info_serivce(orig_json: Annotated[str, "原始信息", True], default_dict: Annotated[dict, "默认字典", True]) -> str:
    """
    根据民事起诉状的所有JSON信息整合成最终需要的JSON信息

    参数:
    orig_json -- 问题 例如: 

    返回结果数量: 1
    返回字段名称: 整合后的JSON
    """
    
    prompt = """
    你是一个专业的法律助手。你的任务是将给定的原始JSON信息与默认字典进行整合，生成一个最终的JSON格式信息。

    请按照以下步骤操作：

    1. 仔细分析提供的原始JSON信息。
    2. 对照默认字典中的每个键。
    3. 如果原始JSON中存在该键，则使用原始JSON中的值。
    4. 如果原始JSON中不存在该键，则使用默认字典中的值。
    5. 确保最终的JSON包含默认字典中的所有键，即使某些键在原始JSON中不存在。
    6. 如原告或者被告是公司，那么原告地址/被告地址即公司的"办公地址"或者"企业地址"。
    7. 如果"原告"或者"被告"字段是"法人"、"总经理"、"董秘"等人物，且原始JSON中存在"法人"、"总经理"、"董秘"等人物的姓名，请你进行替换。

    默认字典如下：
    {default_dict}

    这是原始JSON数据：
    {orig_json}

    请以JSON格式返回提取的信息, 确保返回的JSON格式正确，只包含整合后的信息。不要返回任何额外的解释或文字，也不需要包含开头的 ```json 和结尾的 ```，而是以'{{'开头以'}}'结尾。
    
    请以JSON格式返回整合后的信息：
    """

    full_prompt = prompt.format(orig_json=orig_json, default_dict=json.dumps(default_dict, ensure_ascii=False, indent=2))
    result = call_glm4(full_prompt)

    return result


### 民事起诉状(主函数)
@register_tool
def get_sue_serivce(sue_info: Annotated[str, "基础信息", True]) -> str:
    """
    根据诉讼信息返回民事起诉状(公民起诉公司)的所有字段, sue_info 要求的字段: ['原告', .....] 

    参数:
    sue_info -- 诉讼信息 例如: 

    返回结果数量: 1条
    返回字段名称: ['起诉状']
    """
    
    # 返回字段名称：['法院名称', '法院负责人', '成立日期', '法院地址', '法院联系电话', '法院官网']
    # def get_court_info_service(court_name: Annotated[str, "法院名称", True]) -> DataFrame:

    # 返回字段名称： ['公司名称', '公司简称', '英文名称', '关联证券', '公司代码', '曾用简称', 
    # '所属市场', '所属行业', '成立日期', '上市日期', '法人代表', '总经理' '董秘',''邮政编码', 
    # '注册地址', '办公地址', '联系电话', '传真’,''官方网址', '电子邮箱', '入选指数', '主营业务', 
    # '经营范围', '机构简介', '每股面值', '首发价格', '首发募资净额', '首发主承商']
    # def get_listed_company_info_service(company_name:  Annotated[str, "公司名称", True]) -> DataFrame:

    # 返回字段名称：['公司名称', '登记状态', '统一社会信用代码', '法定代表人', '注册资本', 
    # '成立日期', '企业地址', '联系电话', '联系邮箱', '注册号', '组织机构代码', '参保人数', 
    # '行业一级', '行业二级', '行业三级', '曾用名', '企业简介', '经营范围']。
    # def get_company_register_service(company_name: Annotated[str, "公司名称", True]) -> DataFrame:

    # 返回字段名称：['律师事务所名称', '律师事务所唯一编码', '律师事务所负责人', '事务所注册资本', 
    # '律师事务所成立日期', '律师事务所地址', '通讯电话', '通讯邮箱', '律所登记机关']
    # def get_lawfirm_info_service(law_firm_name: Annotated[str, "律师事务所名称", True] ) -> DataFrame:


    sue_info = json.loads(sue_info)
    print(f"orig_sue_info: {sue_info}")
    # 获取原告身份和被告身份
    plaintiff_identity = sue_info.get("原告身份")
    defendant_identity = sue_info.get("被告身份")
    Defualt_sue_info = generate_sue_info_default_dict(plaintiff_identity, defendant_identity)
    edited_sue_info = {}

    # 遍历 Defualt_sue_info
    for key, default_value in Defualt_sue_info.items():
        # 如果键在 sue_info 中存在，使用 sue_info 的值
        if key in sue_info:
            edited_sue_info[key] = sue_info[key]
        # 如果键在 sue_info 中不存在，使用默认值
        else:
            edited_sue_info[key] = default_value
    
    # print(f"default_dict: {Defualt_sue_info}\nsue_info: {sue_info}\nedited_sue_info: {edited_sue_info}")

    # 原告或者被告与公司有关
    原告公司 = sue_info.get("原告公司")
    被告公司 = sue_info.get("被告公司")
    if 原告公司:
        原告公司信息 = get_listed_company_info_service(company_name=原告公司)
        if 原告公司信息.empty:
            原告公司信息 = get_company_register_service(company_name=原告公司)
        
        edited_sue_info['原告公司信息'] = 原告公司信息.to_dict(orient='records')
    if 被告公司:
        被告公司信息 = get_listed_company_info_service(company_name=被告公司)
        if 被告公司信息.empty:
            被告公司信息 = get_company_register_service(company_name=被告公司)

        edited_sue_info['被告公司信息'] = 被告公司信息.to_dict(orient='records')

    print(f"edited_sue_info: {edited_sue_info}")
    edited_sue_info["原告律所信息"] = get_lawfirm_info_service(law_firm_name=edited_sue_info["原告委托诉讼代理人"]).to_dict(orient='records')
    edited_sue_info["被告律所信息"] = get_lawfirm_info_service(law_firm_name=edited_sue_info["被告委托诉讼代理人"]).to_dict(orient='records')
    edited_sue_info["法院信息"] = get_court_info_service(court_name=edited_sue_info["法院名称"]).to_dict(orient='records')

    # 打印结果（可选）
    # print(f"edited_sue_info_new: {edited_sue_info}")
    edited_sue_info = json.dumps(edited_sue_info, ensure_ascii=False, indent=2)

    # 输入模型输出整理后的结果
    final_edited_sue_info = conform_sue_info_serivce(orig_json = edited_sue_info, default_dict = Defualt_sue_info)
    final_edited_sue_info = json.loads(final_edited_sue_info)
    print(f"详细信息：{final_edited_sue_info}")


    # 调用接口生成起诉书
    if plaintiff_identity == "公民" and defendant_identity == "公民":
        return get_citizens_sue_citizens(final_edited_sue_info)
    elif plaintiff_identity == "公司" and defendant_identity == "公民":
        return get_company_sue_citizens(final_edited_sue_info)
    elif plaintiff_identity == "公民" and defendant_identity == "公司":
        return get_citizens_sue_company(final_edited_sue_info)
    elif plaintiff_identity == "公司" and defendant_identity == "公司":
        return get_company_sue_company(final_edited_sue_info)
    else:
        raise ValueError("无效的身份组合")


#### 格式化审理日期 为YY年MM月DD日
def format_date(date_str):
    # 解析日期字符串
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    # 格式化日期
    formatted_date = dt.strftime(f"{dt.year}年{dt.month}月{dt.day}日")
    return formatted_date



# 自定义转换函数，确保所有值都可以被 JSON 支持
def convert_to_serializable(obj):
    if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.to_list()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    else:
        return obj



@register_tool
def save_all_company_info_to_doc_service(company_name: Annotated[str, "公司名称", True],  company_register_info_path: Annotated[str, "公司工商信息保存路径", True] = '', company_subcompany_info_path: Annotated[str, "公司子公司信息保存路径", True] = '',company_involved_cases_info_path: Annotated[str, "公司工商信息保存路径", True] = '', company_xzgxf_info_path: Annotated[str, "公司工商限制高消费保存路径", True] = '') -> DataFrame:
    """
    根据公司名称，和该公司的工商信息，(全资)子公司信息，涉案信息，限制高消费信息整合成报告，记住上述四种信息都要查询，利用下述工具,get_company_register_service
    ,get_listed_sub_company_info_service_by_parent_company_name/get_listed_all_sub_company_info_service_by_parent_company_name, get_company_involved_cases_info_service, get_company_xzgxf_by_company_name_service获取对应数据信息路径。


    参数:
    company_name -- 公司名称，例如"（2018）鲁0403执1281号"
    company_register_info_path -- 公司工商信息保存路径，例如"XXX_get_company_register_service.csv"
    company_subcompany_info_path -- 公司子公司信息保存路径，例如"XXX_get_listed_sub_company_info_service_by_parent_company_name/get_listed_sub_company_info_service_by_company_name.csv"
    company_involved_cases_info -- 公司涉案信息保存路径，例如"XXXX_get_company_involved_cases_info_service.csv"
    company_xzgxf_info -- 公司限制高消费信息保存路径，例如"XXXX_get_company_xzgxf_by_company_name_service.csv"


    返回结果数量：1条
    返回字段名称：['公司名称','整合报告信息']
    """ 
    try:
        # 尝试读取文件
        company_register_info_df = pd.read_csv(company_register_info_path)
    except:
        # 如果捕获到 EmptyDataError 异常，创建一个空的 DataFrame
        company_register_info_df = pd.DataFrame()
    try:
        # 尝试读取文件
        company_sub_company_info_df = pd.read_csv(company_subcompany_info_path)
    except:
        # 如果捕获到 EmptyDataError 异常，创建一个空的 DataFrame
        company_sub_company_info_df = pd.DataFrame()
    try:
        # 尝试读取文件
        company_involved_cases_info_df = pd.read_csv(company_involved_cases_info_path)
    except:
        # 如果捕获到 EmptyDataError 异常，创建一个空的 DataFrame
        company_involved_cases_info_df = pd.DataFrame()
    try:
        # 尝试读取文件
        company_xzgxf_info_df = pd.read_csv(company_xzgxf_info_path)
    except:
        # 如果捕获到 EmptyDataError 异常，创建一个空的 DataFrame
        company_xzgxf_info_df = pd.DataFrame()

    company_info_dict_df = {}
    ### 工商信息字段变化保存
    company_register_info = {}
    company_register_info['公司名称'] = company_register_info_df['公司名称'][0]
    company_register_info['登记状态'] = company_register_info_df['登记状态'][0]
    company_register_info['统一社会信用代码'] = company_register_info_df['统一社会信用代码'][0]
    company_register_info['参保人数'] = str(company_register_info_df['参保人数'][0])
    company_register_info['行业一级'] = company_register_info_df['行业一级'][0]
    company_register_info['行业二级'] = company_register_info_df['行业二级'][0]
    company_register_info['行业三级'] = company_register_info_df['行业三级'][0]
    company_info_dict_df['工商信息'] = [company_register_info]

    ### 所有子公司信息
    sub_company_info_list = []
    if company_sub_company_info_df.shape[0] > 0:
        for i in range(company_sub_company_info_df.shape[0]):
            company_sub_company_info = {}
            company_sub_company_info['关联上市公司全称'] = company_sub_company_info_df['母公司全称'][i]
            company_sub_company_info['上市公司关系'] = company_sub_company_info_df['母公司关系'][i]
            company_sub_company_info['上市公司参股比例'] = company_sub_company_info_df['母公司参股比例'][i]
            company_sub_company_info['上市公司投资金额'] = str(company_sub_company_info_df['母公司投资金额'][i])
            if '子公司名称' in company_sub_company_info_df.columns:
                company_sub_company_info['公司名称'] = company_sub_company_info_df['子公司名称'][i]
            else:
                company_sub_company_info['公司名称'] = company_sub_company_info_df['全资子公司名称'][i]
   
            sub_company_info_list.append(company_sub_company_info)
  
    company_info_dict_df['子公司信息'] = sub_company_info_list

    
    # 所有涉案信息
    involved_cases_info_list = []
    if company_involved_cases_info_df.shape[0] > 0:
        for i in range(company_involved_cases_info_df.shape[0]):
            involved_cases_info = {}
            involved_cases_info['关联公司'] = company_involved_cases_info_df['关联公司'][i]
            involved_cases_info['原告'] = company_involved_cases_info_df['原告'][i]
            involved_cases_info['被告'] = company_involved_cases_info_df['被告'][i]
            involved_cases_info['案由'] = company_involved_cases_info_df['案由'][i]
            involved_cases_info['涉案金额'] = company_involved_cases_info_df['涉案金额'][i]
            involved_cases_info['日期'] = "TimeStart" + company_involved_cases_info_df['日期'][i] + "TimeEnd"
            involved_cases_info_list.append(involved_cases_info)
    

    company_info_dict_df['裁判文书'] = involved_cases_info_list
 
    # 所有限制高消费信息
    xzgxf_info_list = []
    if company_xzgxf_info_df.shape[0] > 0:

        for i in range(company_xzgxf_info_df.shape[0]):
            xzgxf_info = {}
            xzgxf_info['限制高消费企业名称'] = company_xzgxf_info_df['限制高消费企业名称'][i]
            xzgxf_info['案号'] = company_xzgxf_info_df['案号'][i]
            xzgxf_info['申请人'] = company_xzgxf_info_df['申请人'][i]
            xzgxf_info['涉案金额'] = company_xzgxf_info_df['涉案金额'][i]
            xzgxf_info['立案日期'] = "TimeStart" + company_xzgxf_info_df['立案日期'][i] + "TimeEnd"
            xzgxf_info['限高发布日期'] = "TimeStart" +  company_xzgxf_info_df['限高发布日期'][i]  + "TimeEnd"
            xzgxf_info_list.append(xzgxf_info)
    company_info_dict_df['限制高消费'] = xzgxf_info_list




    report_str = json.dumps(company_info_dict_df,default=convert_to_serializable, ensure_ascii=False)
    report_str = report_str.replace('\n', '')
    report_str = report_str.replace('\"', '\'')
    report_str = report_str.replace('TimeEnd\'', '\')')
    report_str = report_str.replace('\'TimeStart', 'Timestamp(\'')
    report_str = report_str.replace('NaN', '\'-\'')

    print(report_str)
    # 获取公司注册信息
    domain = "https://comm.chatglm.cn"

    url = f"{domain}/law_api/s1_b/save_dict_list_to_word"
    data = {
        'company_name': company_name,
        'dict_list': report_str
    }
    rsp = requests.post(url, json=data, headers=headers)
    res = rsp.text
    df = pd.DataFrame([[company_name, res]], columns=['公司名称','整合报告信息'])
    
    return  df