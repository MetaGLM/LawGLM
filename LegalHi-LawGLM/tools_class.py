"""
Author: lihaitao
Date: 2024-07-06 00:54:49
LastEditors: Do not edit
LastEditTime: 2024-07-28 23:24:21
FilePath: /GLM2024/GLM4-B-dev/tools_class.py
"""

from tool_register.register import *
from tool_register.tools import *


CompanyInfo_tools = []
CompanyInfo_tools.append(register_tool_one(get_company_info))
CompanyRegister_tools = []
CompanyRegister_tools.append(register_tool_one(get_company_register))
CompanyRegister_tools.append(register_tool_one(get_company_register_name))
SubCompanyInfo_tools = []
SubCompanyInfo_tools.append(register_tool_one(get_sub_company_info))
SubCompanyInfo_tools.append(register_tool_one(get_sub_company_info_list))
LegalDocInfo_tools = []
LegalDocInfo_tools.append(register_tool_one(get_legal_document))
LegalDocInfo_tools.append(register_tool_one(get_legal_document_list))
Court_tools = []
Court_tools.append(register_tool_one(get_court_info))
Court_tools.append(register_tool_one(get_court_code))
Law_tools = []
Law_tools.append(register_tool_one(get_lawfirm_info))
Law_tools.append(register_tool_one(get_lawfirm_log))
Address_tools = []
Address_tools.append(register_tool_one(get_address_info))
Address_tools.append(register_tool_one(get_address_code))
TempInfo_tools = []
TempInfo_tools.append(register_tool_one(get_temp_info))
Abstract_tools = []
Abstract_tools.append(register_tool_one(get_legal_abstract))
XzgxfInfo_tools = []
XzgxfInfo_tools.append(register_tool_one(get_xzgxf_info))
XzgxfInfo_tools.append(register_tool_one(get_xzgxf_info_list))


Tools_map = {
    "CompanyInfo": CompanyInfo_tools,
    "CompanyRegister": CompanyRegister_tools,
    "SubCompanyInfo": SubCompanyInfo_tools,
    "LegalDoc": LegalDocInfo_tools,
    "CourtInfo": Court_tools,
    "CourtCode": Court_tools,
    "LawfirmInfo": Law_tools,
    "LawfirmLog": Law_tools,
    "AddrInfo": Address_tools,
    "AddrCode": Address_tools,
    "TempInfo": TempInfo_tools,
    "LegalAbstract": Abstract_tools,
    "XzgxfInfo": XzgxfInfo_tools,
}


Tools_prompt = {
    "CompanyInfo": "CompanyInfo表格可以使用的API_tool包括 1.get_company_info: 根据[公司名称]、[公司简称]或[公司代码]查找上市公司信息，遇到公司简称只使用这个表格。",
    "CompanyRegister": "CompanyRegister表格可以使用的API_tool包括 1.get_company_register: 根据[公司名称]查询工商信息 2.get_company_register_name: 根据[统一社会信用代码]查询[公司名称]",
    "SubCompanyInfo": "SubCompanyInfo表格可以使用的API_tool包括 1.get_sub_company_info: 根据被投资的子[公司名称]获得表格内其他字段信息 2.get_sub_comp any_info_list: 根据[关联上市公司全称]称查询该公司投资的所有子公司信息list",
    "LegalDoc": "LegalDoc表格可以使用的API_tool包括 1.get_legal_document: 根据[案号]查询裁判文书相关信息 2.get_legal_document_list: 根据[关联公司]查询所有裁判文书相关信息list",
    "CourtInfo": "CourtInfo表格可以使用的API_tool包括 1.get_court_info: 根据[法院名称]查询表格相关信息",
    "CourtCode": "CourtCode表格可以使用的API_tool包括 1.get_court_code: 根据[法院名称]或者[法院代字]查询表格等相关数据，遇到法院代字只使用这个表格。",
    "LawfirmInfo": "LawfirmInfo可以使用的API_tool包括 1.get_lawfirm_info: 根据[律师事务所名称]查询表格相关信息",
    "LawfirmLog": "LawfirmLog表格可以使用的API_tool包括 1.get_lawfirm_log: 根据[律师事务所名称]查询表格相关信息",
    "AddrInfo": "AddrInfo表格可以使用的API_tool包括 1.get_address_info: 根据[地址]查该地址对应的省份城市区县",
    "AddrCode": "AddrCode表格可以使用的API_tool包括 1.get_address_code: 根据[省份][城市][区县]查询区划代码",
    "TempInfo": "TempInfo表格可以使用的API_tool包括 1.get_temp_info: 根据[日期]及[省份][城市]查询天气相关信息",
    "LegalAbstract": "LegalAbstract表格可以使用的API_tool包括 1.get_legal_abstract: 根据[案号]查询文本摘要",
    "XzgxfInfo": "XzgxfInfo表格可以使用的API_tool包括 1.get_xzgxf_info: 根据[案号]查询限制高消费相关信息 2.get_xzgxf_info_list: 根据[限制高消费企业名称]查询所有限制高消费相关信息list",
}


# get_company_info_explain = """
# get_company_info工具根据上市公司名称、简称或代码查找上市公司信息。
# 示例输入:
# {"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []}
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
# need_fields可填的字段包括以下信息: ["公司名称", "公司简称", "英文名称", "关联证券", "公司代码", "曾用简称", "所属市场", "所属行业", "上市日期", "法人代表", "总经理", "董秘", "邮政编码", "注册地址", "办公地址", "联系电话", "传真", "官方网址", "电子邮箱", "入选指数", "主营业务", "经营范围", "机构简介", "每股面值", "首发价格", "首发募资净额", "首发主承销商"]
# """


# get_company_register_explain = """
# get_company_register工具根据公司名称，查询工商信息。
# 示例输入:
# {"query_conds": {"公司名称": "天能电池集团股份有限公司"}, "need_fields": []}
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
# need_fields可填的字段包括以下信息: ["公司名称", "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "企业简介", "经营范围"]
# """

# get_company_register_name_explain = """
# get_company_register_name工具根据统一社会信用代码查询公司名称.
# 示例输入:{"query_conds": {"统一社会信用代码": ''}, "need_fields": ["公司名称"]}
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

# 以下是参考例子：
# 输入参数：
# {"need_fields":{"Items":["公司名称"]},"query_conds":{"统一社会信用代码":"91310000677833266F"}}
# 输出结果：
# {"need_fields":["公司名称"],"query_conds":{"统一社会信用代码":"91310000677833266F"}}
# 例子结束

# 请判断以上输入参数是否正确并输出正确的输入格式。
# 按照以下json格式进行输出，可以被Python json.loads函数解析。只给出问题分解结果，不作解释，不作答：
# ```json
# {{
#    "need_fields":
#    "query_conds":
# }}
# ```

# """


# get_legal_document_list_explain = """
# get_legal_document_list工具根据关联公司查询所有裁判文书相关信息list
# 示例输入:{"query_conds": {"关联公司": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []}
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段。
# query_conds只有关联公司一个key，need_fields是一个列表，列表的每个元素是字符串。
# 确保你的回应必须严格遵循上述格式。

# 以下是参考例子：
# 输入参数：{'need_fields': {'Items': ['案号']}, 'query_conds': {'关联公司': '信息产业电子第十一设计研究院科技工程股份有限公司', '日期': {'$gte': '2020-01-01', '$lte': '2020-12-31'}, '文书类型': '民事初审'}}
# 正确参数：{"need_fields":["日期","案号"],"query_conds":{"关联公司":"信息产业电子第十一设计研究院科技工程股份有限公司"}}

# 输入参数：{"need_fields":{"Items":["涉案金额"]},"query_conds":{"关联公司":"廊坊市凯宏家居广场有限公司","日期":"2019"}}
# 正确参数：{"need_fields":{"Items":["日期","涉案金额"]},"query_conds":{"关联公司":"廊坊市凯宏家居广场有限公司"}}

# 输入参数：(arguments='{"need_fields":{"Items":["案号","涉案金额"]},"query_conds":{"关联公司":"山东省戴瑞克新材料有限公司","日期":"2021年","案由":"劳务及劳务者相关的纠纷案件"}
# 正确参数：(arguments='{"need_fields":{"Items":["日期","案由","案号","涉案金额"]},"query_conds":{"关联公司":"山东省戴瑞克新材料有限公司"}
# """

# get_court_code_explain = """
# get_court_code工具根据法院名称或者法院代字查询法院代字等相关数据
# 示例输入:{"query_conds": {"法院名称": "怀远县人民法院"}, "need_fields": []}
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段。
# query_conds只有一个key，为"法院名称"或"法院代字"，need_fields是一个列表，列表的每个元素是字符串。
# 确保你的回应必须严格遵循上述格式。

# 以下是参考例子：
# 输入参数：{'need_fields': {'Items': ['法院代字']}, 'query_conds': {"案号":"(2020)川3433民初1572号"}}
# 正确参数：{"need_fields":["法院名称"],"query_conds":{"法院代字":"川3433"}}
# """

# other_expalain = """
# need_fields是一个列表，列表的每个元素是字符串。
# need_fields传入空列表，则表示返回所有字段，否则返回填入的字段。
# 如果need_fields出现了不应存在的字符，则将need_fields置空。
# query_conds不要加入不符合格式的信息！！
# query_conds不要加入不符合格式的信息！！
# query_conds不要加入不符合格式的信息！！

# 以下是参考例子：
# 例子1:
# 输入参数：
# {"need_fields":{"Items":["日期","涉案金额"]},"query_conds":{"关联公司":"上海晨光文具股份有限公司","文书类型":"判决书"}}
# 输出结果：
# {"need_fields":["日期","涉案金额"],"query_conds":{"关联公司":"上海晨光文具股份有限公司"}}

# 例子2:
# 输入参数：
# {"need_fields":{"Items":null},"query_conds":{"关联公司":"上海晨光文具股份有限公司","文书类型":"判决书"}}
# 输出结果：
# {"need_fields":[],"query_conds":{"关联公司":"上海晨光文具股份有限公司"}}

# 例子3:
# 输入参数：
# {"need_fields":{"Items":[]},"query_conds":{"关联公司":"上海晨光文具股份有限公司"}}
# 输出结果：
# {"need_fields":[],"query_conds":{"关联公司":"上海晨光文具股份有限公司"}}

# 例子4:
# 输入参数：
# {"need_fields":["原告律师事务所"],"query_conds":{"原告":"安徽邦瑞新材料科技有限公司"}}
# 输出结果：
# {"need_fields":["原告律师事务所"],"query_conds":{"关联公司":"安徽邦瑞新材料科技有限公司"}}

# """


# API_map = {'get_company_info': get_company_info_explain,
#            'get_company_register':get_company_register_explain,
#            'get_company_register_name': get_company_register_name_explain,
#            'get_legal_document_list':other_expalain,
#            'get_court_code': get_court_code_explain
#            }
