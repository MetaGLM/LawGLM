from api import call_api
from fuzzywuzzy import fuzz
from copy import deepcopy
import re
import contextlib
import io





# 法院|get_court_code_by_case_number
# 根据`案号`匹配法院代字，然后查询`CourtCode`表格，可以["法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"]获取性能稳定
def get_court_code_by_case_number(param):
    """
    根据案号查询法院信息："法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"，不可以获取法院地点，
    其中案号格式为：(+收案年度+)+法院代字+类型代字+案件编号+号
    :param param: {'query_conds': {'案号': 'str'}, "need_fields": ["法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"]}
    :return:
    """
    # 实现过程略





# /get_legal_document_list|filter_legal_docs|LegalDoc
# 过滤法律文档信息，从法律文档列表中过滤出符合条件的文档，支持legal_documents表中的字段，如原告被告律师事务所等，但是不支持胜诉方等
def filter_legal_docs(legal_documents_result, filter_dict):
    """
    过滤法律文档信息
    根据指定的过滤条件，从法律文档列表中过滤出符合条件的文档。案号格式为：(+收案年度+)+法院代字+类型代字+案件编号+号。
    参数:
    legal_documents_result (list[dict]): 通过 get_legal_document_list 接口获得的法律文档列表。
    param filter_dict (dict): 包含过滤条件的字典
        - 案由 (str): 案件的案由，支持模糊匹配，但是必须是关键词例如:劳务纠纷,债权纠纷，侵害商标权纠纷。
        - 年份 (str): 案件的年份，例如 '2019'。
        - 年份类型 (str): 年份的类型，可以是 '立案日期'、'起诉日期' 或 '审理日期'。
        - 审理省份: (str) 案件审理的省份，注意是简称，例如 安徽省->皖 四川->川
        - 案件类型 (str): 案件类型，可以是 ['民', '民初', '民终', '执','民申'] 之一。
            - '民': 民事诉讼
            - '民初': 民事诉讼初审
            - '民终': 民事诉讼终审
            - '执': 执行案件
        - 原告 (str): 案件的原告。
        - 被告 (str): 案件的被告。
        - 最小涉案金额 (str): 案件的最小涉案金额，支持 1亿，10万这种描述,涉案金额不为0的填“0”
        - 最大涉案金额 (str): 案件的最大涉案金额，支持 1亿，10万这种描述
        - 法院代字(str): 审理法院的代字
    注意：字段只有在需要的时候才存在，例如筛选2019年的执行案件只需要{'年份':'2019','年份类型':'立案日期','案件类型':'执'}。
    返回:
        list[dict]: 包含符合条件的法律文档信息的列表。
    """
    # 实现过程略





# /get_sub_company_info_list|filter_sub_company|SubCompanyInfo
# 子公司过滤辅助函数,输入关联上市公司全称 金额范围 持股范围 可以通过市公司投资金额和上市公司参股比例筛选子公司
def filter_sub_company(sub_company_list, filter_dict):
    """
    过滤子公司信息
    :param sub_company_list:  /get_sub_company_info_list 返回的结果
    :param filter_dict: dict 包含过滤参数的字典
        - 最小投资金额: str 最小上市公司投资金额（例如 "1亿", "500万"）默认为 -1
        - 最大投资金额: str 最大上市公司投资金额（例如 "1亿", "500万"）默认为inf
        - 最小持股比例: str|int 最小上市公司参股比例，支持 0-100 的百分制，默认为0
        - 最大持股比例: str|int 最大上市公司参股比例，支持 0-100 的百分制，默认为100
        注意：字段只有在需要的时候才存在，例如筛选全资子公司只需要:{'最小持股比例':100}，没有其他字段。
            特别的，最小上市公司投资金额为大于，其余都包含等于，例如：{'最小上市公司投资金额':0} 会筛选大于0的
    :return: list[dict] 包含符合条件的子公司信息的列表，每个子公司信息以字典形式表示
    """
    # 实现过程略




# /get_xzgxf_info_list|filter_xzgxf_info_list|XzgxfInfo
# 限制高消费过滤函数，支持将 /get_xzgxf_info_list的结果传入并按照条件过滤
def filter_xzgxf_info_list(xzgxf_info_list, filter_dict):
    """
    过滤限制高消费信息列表
    :param xzgxf_info_list: list[dict] 包含行政限高信息的列表
    :param filter_dict: dict 包含过滤条件的字典
        - 审理省份: str 案件审理的省份，注意是简称，例如 安徽省->皖 四川->川
        - 立案时间: str 案件的立案时间年份，例如 '2019'
        - 限高发布日期: str 限高的发布日期年份，例如 '2019'
        - 最小涉案金额: str 默认 "-1" 采用的是大于 例如 输入 ”0“ 则筛选涉案金额大于0，支持 "1万"，”1亿“，不支持汉字的 ”一万“
        - 最大涉案金额: str 默认 "inf" 采用的是小于
    注意：字段只有在需要的时候才存在，例如筛选2020年再安徽立案的案件只需要：{'立案时间':'2020','审理省份':'皖'}
    :return: list[dict] 包含符合条件的行政限高信息的列表
    """
    # 实现过程略




# 级别.*法院|法院.*级别|sort_court_level
# 将法院按照从高到低进行排序
def sort_court_level(case_num_list,level_type='法院级别'):
    """
    :param case_num_list: list[dict] or list 案号列表或者 [{"案号":str}],可以直接传入接口结果
    :param level_type: 法院级别 或者 行政级别
    :return:List[Dict['案号','法院名称']] 排序后的结果
    """

    # 实现过程略




# .
# 可以转化字符串成数字
def map_str_to_num(str_num):
    '''
    :param str_num: int|float|str 一些数字 "1万" '1000'  1000.
    return  float
    '''
    # 实现过程略