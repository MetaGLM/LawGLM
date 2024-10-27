from config import *

# import List

# from model import call_glm
#
# query = '什么是金融监管？'
# messages = [
#         {"role": "system", "content": '你是一个法律专家，请根据你的专业知识回答用户的问题。请尽可能简答问题'},
#         {"role": "user", "content": query}
#     ]
#
# response = call_glm(messages, model="glm-4-0520")
# print_log(response)


# 返回list需要检查返回值类型，如果数量为一那么可能是dict而不是list

# 0   get_company_info                只能是：公司名称or公司简称or公司代码 或组合  CompanyInfo
# 1   get_company_register            只能是：公司名称                   CompanyRegister
# 2   get_company_register_name       只能是：统一社会信用代码             公司名
# 3   get_sub_company_info            只能是：公司名称                   SubCompanyInfo
# 3   get_sub_company_info_list       只能是：关联上市公司全称             List[SubCompanyInfo]
# 4   get_legal_document              只能是：案号                      LegalDoc
# 5   get_legal_document_list         只能是：关联公司                   List[LegalDoc]
# 6   get_court_info                  只能是：法院名称                   CourtInfo
# 7   get_court_code                  只能是：法院名称或者法院代字          CourtCode
# 8   get_lawfirm_info                只能是：律师事务所名称               LawfirmInfo
# 9   get_lawfirm_log                 只能是：律师事务所名称               LawfirmLog
# 10   get_address_info               只能是：地址                       AddrInfo
# 11   get_address_code               只能是：省份,城市,区县三者组合        AddrCode
# 12   get_temp_info                  只能是：日期,省份,城市三者组合        TempInfo
# 13   get_legal_abstract             只能是：案号                       LegalAbstract
# 14   get_xzgxf_info                 只能是：案号                       XzgxfInfo
# 15   get_xzgxf_info_list            只能是：限制高消费企业名称            List[XzgxfInfo]


import requests

team_token = "140B8B7781A83577CA4A74B139289281E38A912F0F09569B"
headers = {"Content-Type": "application/json", "Authorization": "Bearer {team_token}".format(team_token=team_token)}
domain = "https://comm.chatglm.cn"

url = f"{domain}/law_api/s1_b/get_company_info"
data = {"query_conds": {"公司名称": "航天机电公司"}, "need_fields": []}
data = {"query_conds": {"公司代码": "300164"}, "need_fields": []}
data = {"query_conds": {"公司简称": "上海建工公司"}, "need_fields": []}
#
# url = f"{domain}/law_api/s1_b/get_company_register"
# data = {"query_conds": {"公司名称": "航天机电公司"}, "need_fields": []}

# #
# #
# url = f"{domain}/law_api/s1_b/get_company_register_name"
# data = {"query_conds": {"统一社会信用代码": "913412825518487107"}, "need_fields": []}
#
# url = f"{domain}/law_api/s1_b/get_sub_company_info"
# data = {"query_conds": {"公司名称": "航天机电公司"}, "need_fields": []}
# # #
# # #
# url = f"{domain}/law_api/s1_b/get_sub_company_info_list"
# data = {"query_conds": {"关联上市公司全称": "上海建工公司"}, "need_fields": []}
# #
#
# url = f"{domain}/law_api/s1_b/get_legal_document"
# data = {"query_conds": {"案号": "(2019)川01民初1949号",}, "need_fields": []}
#'{"case_number":"(2021)辽01民终16020号"}'
# (2021)辽01民终16020号
url = f"{domain}/law_api/s1_b/get_legal_document_list"
data = {
    "query_conds": {
        "关联公司": "上海建工公司",
    },
    "need_fields": [],
}
# data = {"query_conds": {"关联公司": "深圳市智动力精密技术股份有限公司",}, "need_fields": []}
# # # # #
# #
# #
# url = f"{domain}/law_api/s1_b/get_court_info"
# data = {"query_conds": {"法院名称": "阜阳市颍东区人民法院"}, "need_fields": []}
#'案号' = {str} '(2019)皖0123民初3454号'
# '案号' = {str} '(2019)皖01民终9939号'
#
#
# url = f"{domain}/law_api/s1_b/get_court_code"
# data = {"query_conds": {'法院名称': '北京市丰台区人民法院'}, "need_fields": ['法院名称']}
# data = {"query_conds": {'法院代字': '辽01'}, "need_fields": []}
#
#
# url = f"{domain}/law_api/s1_b/get_lawfirm_info"
# data = {"query_conds": {"律师事务所名称": "北京盈科（义乌）律师事务所"}, "need_fields": []}
#
#
# url = f"{domain}/law_api/s1_b/get_lawfirm_log"
# data = {"query_conds": {"律师事务所名称": "北京盈科（义乌）律师事务所"}, "need_fields": []}
#
# url = f"{domain}/law_api/s1_b/get_address_info"
# data = {"query_conds": {"地址": "合肥市高新区科学大道91"}, "need_fields": []}
#
#
# url = f"{domain}/law_api/s1_b/get_address_code"
# data = {"query_conds": {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}, "need_fields": []}
# data = {"query_conds": {"省份": "江苏省", "城市": "连云港市", "区县": "高新技术产业开发区"}, "need_fields": []}
# data = {"query_conds": {"省份": "重庆市", "城市": "重庆市", "区县": "南岸区"}, "need_fields": []}
#
# url = f"{domain}/law_api/s1_b/get_temp_info"
# data = 	{"query_conds": {"省份": "四川省", "城市": "成都市", "日期": "2019年12月11日"}, "need_fields": []}
# data = 	{"query_conds": {"省份": "浙江省", "城市": "杭州市", "日期": "2020年4月3日"}, "need_fields": []}
# '{"date": "2020年11月06日", "province": "新疆维吾尔自治区", "city": "吐鲁番市"}'
# 根据浙江省杭州市和日期2020年4月3日
#
# #
# url = f"{domain}/law_api/s1_b/get_legal_abstract"
# data = {"query_conds": {"案号": "（2019）沪0115民初61975号"}, "need_fields": []}
# #
# url = f"{domain}/law_api/s1_b/get_xzgxf_info"
# data = { "query_conds": {"案号": "（2023）津0116执29434号"}, "need_fields": [] }

# url = f"{domain}/law_api/s1_b/get_xzgxf_info_list"
# data = { "query_conds": {"限制高消费企业名称": "龙元建设集团股份有限公司"}, "need_fields": [] }
#
#
#
# url = f"{domain}/law_api/s1_b/get_sum"
# data = 	["2500.00万", "7247.52万", "7532.43万", "100.00万"]
#
# url = f"{domain}/law_api/s1_b/rank"
# data = 	{ "keys": ["a", "b", "c"], "values": ["1", "12", "3"] }
#
# url = f"{domain}/law_api/s1_b/get_citizens_sue_citizens"
# data = {'原告': '张三', '原告法定代表人': '张三','原告性别': '男', '原告生日': '1976-10-2', '原告民族': '汉', '原告工作单位': 'XXX',
#         '原告地址': '中国', '原告联系方式': '123456', '原告委托诉讼代理人': '李四',
#         '原告委托诉讼代理人联系方式': '421313', '被告': '王五', '被告性别': '女', '被告生日': '1975-02-12',
#         '被告民族': '汉', '被告工作单位': 'YYY', '被告地址': '江苏', '被告联系方式': '56354321',
#         '被告委托诉讼代理人': '赵六', '被告委托诉讼代理人联系方式': '09765213', '诉讼请求': 'AA纠纷',
#         '事实和理由': '上诉', '证据': 'PPPPP', '法院名称': '最高法', '起诉日期': '2012-09-08'}


# rsp = requests.post(url, json=data, headers=headers)
# print(rsp.json())

url = f"{domain}/law_api/s1_b/save_dict_list_to_word"
data = {
    "company_name": "北京碧水源科技股份有限公司",
    "dict_list": "{'工商信息': [{'公司名称': '北京碧水源科技股份有限公司', '登记状态': '存续', '统一社会信用代码': '91110000802115985Y', '参保人数': '351', '行业一级': '科学研究和技术服务业', '行业二级': '科技推广和应用服务业', '行业三级': '其他科技推广服务业'}], '子公司信息': [{'关联上市公司全称': '北京碧水源科技股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': 100.0, '上市公司投资金额': '1.06亿', '公司名称': '北京碧海环境科技有限公司'}], '裁判文书': [{'关联公司': '北京碧水源科技股份有限公司', '原告': '四川帝宇水利水电工程有限公司', '被告': '成都碧水源江环保科技有限公司,北京碧水源科技股份有限公司', '案由': '建设工程施工合同纠纷', '涉案金额': 0.0, '日期': Timestamp('2019-07-23 00:00:00')}], '限制高消费': [{'限制高消费企业名称': '南京仙林碧水源污水处理有限公司', '案号': '（2024）苏0113执1601号', '申请人': '苏华建设集团有限公司', '涉案金额': '-', '立案日期': Timestamp('2024-04-07 00:00:00'), '限高发布日期': Timestamp('2024-06-24 00:00:00')}]}",
}
# data = {'company_name': '北京碧水源科技股份有限公司',
#         'dict_list': "{'工商信息': [{'登记状态': '存续', '统一社会信用代码': '91110000802115985Y', '参保人数': '351', '行业一级': '科学研究和技术服务业', '行业二级': '科技推广和应用服务业', '行业三级': '其他科技推广服务业'}], '子公司信息': [], '裁判文书': [], '限制高消费': []}"}
# # data = {'company_name': '北京碧水源科技股份有限公司',
# #         'dict_list': "{'工商信息': [], '子公司信息': [{'关联上市公司全称': '北京碧水源科技股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': 100.0, '上市公司投资金额': '1.06亿', '公司名称': '北京碧海环境科技有限公司'}], '裁判文书': [{'关联公司': '北京碧水源科技股份有限公司', '原告': '四川帝宇水利水电工程有限公司', '被告': '成都碧水源江环保科技有限公司,北京碧水源科技股份有限公司', '案由': '建设工程施工合同纠纷', '涉案金额': 0.0, '日期': Timestamp('2019-07-23 00:00:00')}], '限制高消费': [{'限制高消费企业名称': '南京仙林碧水源污水处理有限公司', '案号': '（2024）苏0113执1601号', '申请人': '苏华建设集团有限公司', '涉案金额': '-', '立案日期': Timestamp('2024-04-07 00:00:00'), '限高发布日期': Timestamp('2024-06-24 00:00:00')}]}"}
#
rsp = requests.post(url, json=data, headers=headers)
print_log(rsp.text)
# # open("1.docx", "wb").write(rsp.content)
