import requests
import re
import logging
import inspect
import sys
import json

logger = logging.getLogger("default")
logger_clean = logging.getLogger("clean")

domain = "comm.chatglm.cn"

tk = "76272BC9ACCE1E701EFC55F390B13813E6FBF3F6A745D9E7" #replace as team token in https://tianchi.aliyun.com/competition/entrance/532221/team
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {tk}'
}

real_post = requests.post
def post_wrapper(url, **kargs):
    data = kargs['json']
    headers=  kargs['headers']
    func_name = url.split('/')[-1].strip()
    js = json.dumps([func_name, data['query_conds']], ensure_ascii=False)
    print(f'参考数据格式{js}')
    #logger_clean.info(f"debug postwraper ={js} input={url, data}")
    return real_post(url, json=data, headers=headers)
requests.post = post_wrapper

class WrapDict(dict):
    def __getitem__(self, key, *args, **kwargs):
        res = super().__getitem__(key, *args, **kwargs)
        js = json.dumps(['data', {key:res}], ensure_ascii=False)
        print(f'参考数据格式{js}')
        return res
    def get(self, key, *args, **kwargs):
        res = super().get(key, *args, **kwargs)
        js = json.dumps(['data', {key:res}], ensure_ascii=False)
        print(f'参考数据格式{js}')
        return res

def wrap_the_return(rsp):
    if type(rsp) == dict:
        return WrapDict(rsp)
    elif type(rsp) == list:
        return [wrap_the_return(x) for x in rsp]
    else:
        return rsp

def deco_get(func):
    def gets(*args, **kwargs):
        rsp = func(*args, **kwargs)
        return wrap_the_return(rsp)
    return gets


#0	根据上市公司名称、简称或代码查找上市公司信息	/law_api/s1_b/get_company_info	query_conds: dict need_fields: list	CompanyInfo	{"query_conds": {"公司名称": "上海妙可蓝多食品科技股份有限公司"}, "need_fields": []} # need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
def get_company_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_company_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_company_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_company_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_company_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_company_info called, hit, args={data}, rsp={rsp}")
        return rsp


#1	根据公司名称，查询工商信息	/law_api/s1_b/get_company_register	query_conds: dict need_fields: list	CompanyRegister	{"query_conds": {"公司名称": "天能电池集团股份有限公司"}, "need_fields": []}
def get_company_register(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_company_register query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_company_register"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_company_register exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_company_register called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_company_register called, hit, args={data}, rsp={rsp}")
        return rsp


#2	根据统一社会信用代码查询公司名称	/law_api/s1_b/get_company_register_name	query_conds: dict need_fields: list	公司名称: str	{"query_conds": {"统一社会信用代码": "913305007490121183"}, "need_fields": []}
def get_company_register_name(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_company_register_name query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_company_register_name"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_company_register_name exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_company_register_name called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_company_register_name called, hit, args={data}, rsp={rsp}")
        return rsp


#3	根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息	/law_api/s1_b/get_sub_company_info	query_conds: dict need_fields: list	SubCompanyInfo	{"query_conds": {"公司名称": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []}
def get_sub_company_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_sub_company_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_sub_company_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_sub_company_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_sub_company_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_sub_company_info called, hit, args={data}, rsp={rsp}")
        return rsp


#4	根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list	/law_api/s1_b/get_sub_company_info_list	query_conds: dict need_fields: list	List[SubCompanyInfo]	{"query_conds": {"关联上市公司全称": "上海航天汽车机电股份有限公司"}, "need_fields": []}
def get_sub_company_info_list(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_sub_company_info_list query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_sub_company_info_list"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_sub_company_info_list exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list and len(rsp) != 0:
        logger.info(f"get_sub_company_info_list called, hit, args={data}, rsp={rsp[:2]}")
        return rsp
    elif type(rsp) == dict and len(rsp) != 0:
        logger.info(f"get_sub_company_info_list called, hit, args={data}, rsp={rsp}")
        return [rsp]
    else:
        logger.info(f"get_sub_company_info_list called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")


#7	根据法院名称查询法院名录相关信息	/law_api/s1_b/get_court_info	query_conds: dict need_fields: list	CourtInfo	{"query_conds": {"法院名称": "上海市浦东新区人民法院"}, "need_fields": []}
def get_court_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_court_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_court_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_court_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_court_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_court_info called, hit, args={data}, rsp={rsp}")
        return rsp


#8	根据法院名称或者法院代字查询法院代字等相关数据	/law_api/s1_b/get_court_code	query_conds: dict need_fields: list	CourtCode	{"query_conds": {"法院名称": "上海市浦东新区人民法院"}, "need_fields": []}
def get_court_code(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_court_code query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_court_code"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_court_code exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_court_code called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_court_code called, hit, args={data}, rsp={rsp}")
        return rsp
    
#9	根据律师事务所查询律师事务所名录	/law_api/s1_b/get_lawfirm_info	query_conds: dict need_fields: list	LawfirmInfo	{"query_conds": {"律师事务所名称": "爱德律师事务所"}, "need_fields": []}
def get_lawfirm_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_lawfirm_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_lawfirm_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_lawfirm_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_lawfirm_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_lawfirm_info called, hit, args={data}, rsp={rsp}")
        return rsp


#10	根据律师事务所查询律师事务所统计数据	/law_api/s1_b/get_lawfirm_log	query_conds: dict need_fields: list	LawfirmLog	{"query_conds": {"律师事务所名称": "北京市金杜律师事务所"}, "need_fields": []}
def get_lawfirm_log(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_lawfirm_log query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_lawfirm_log"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_lawfirm_log exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_lawfirm_log called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_lawfirm_log called, hit, args={data}, rsp={rsp}")
        return rsp

casenum_patn = "\((\d+)\)([\u4e00-\u9fa5]+)(\d*)([\u4e00-\u9fa5]+)(\d+)号"
def prep_proc(legal_doc):
    jday = legal_doc.pop('日期')
    casename = legal_doc['案号']
    casename = casename.replace("（", "(").replace("）", ")")
    legal_doc['案号'] = casename
    legal_doc['审理日期'] = jday
    try:
        yr, court_p, court_code, type_p, type_code = re.findall(casenum_patn, casename)[0]
        legal_doc['起诉日期'] = f'{yr}年'
        legal_doc['法院代字'] = f'{court_p}{court_code}'
    except Exception as ex:
        print(ex,casename)
    return legal_doc

#5	根据案号查询裁判文书相关信息	/law_api/s1_b/get_legal_document	query_conds: dict need_fields: list	LegalDoc	{"query_conds": {"案号": "(2019)沪0115民初61975号"}, "need_fields": []}
def get_legal_document(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_legal_document query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_legal_document"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_legal_document exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_legal_document called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_legal_document called, hit, args={data}, rsp={rsp}")
        return prep_proc(rsp)
    
#14	根据案号查询文本摘要	/law_api/s1_b/get_legal_abstract	query_conds: dict need_fields: list	LegalDoc	{"query_conds": {"案号": "（2019）沪0115民初61975号"}, "need_fields": []}
def get_legal_abstract(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_legal_abstract query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_legal_abstract"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_legal_abstract exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_legal_abstract called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_legal_abstract called, hit, args={data}, rsp={rsp}")
        return rsp
    
#6	根据关联公司查询所有裁判文书相关信息list	/law_api/s1_b/get_legal_document_list	query_conds: dict need_fields: list	List[LegalDoc]	{"query_conds": {"关联公司": "上海爱斯达克汽车空调系统有限公司"}, "need_fields": []}
def get_legal_document_list(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_legal_document_list query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_legal_document_list"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_legal_document_list exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list and len(rsp) != 0:
        logger.info(f"get_legal_document_list called, hit, args={data}, rsp={rsp[:2]}")
        return [prep_proc(q) for q in rsp]
    elif type(rsp) == dict and len(rsp) != 0:
        logger.info(f"get_legal_document_list called, hit, args={data}, rsp={rsp}")
        return [prep_proc(rsp)]
    else:
        logger.info(f"get_legal_document_list called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")



#16	根据企业名称查询所有限制高消费相关信息list	/law_api/get_xzgxf_info_list	query_conds: dict need_fields: list	List[XzgxfInfo]	{ "query_conds": {"限制高消费企业名称": "欣水源生态环境科技有限公司"}, "need_fields": [] }
def get_xzgxf_info_list(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_xzgxf_info_list query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_xzgxf_info_list"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_xzgxf_info_list exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list and len(rsp) != 0:
        logger.info(f"get_xzgxf_info_list called, hit, args={data}, rsp={rsp[:2]}")
        return rsp
    elif type(rsp) == dict and len(rsp) != 0:
        logger.info(f"get_xzgxf_info_list called, hit, args={data}, rsp={rsp}")
        return [rsp]
    else:
        logger.info(f"get_xzgxf_info_list called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    
    
#15	根据案号查询限制高消费相关信息	/law_api/s1_b/get_xzgxf_info	query_conds: dict need_fields: list	XzgxfInfo	{ "query_conds": {"案号": "（2018）鲁0403执1281号"}, "need_fields": [] }
def get_xzgxf_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_xzgxf_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_xzgxf_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_xzgxf_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_xzgxf_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_xzgxf_info called, hit, args={data}, rsp={rsp}")
        return rsp
    


#11	根据地址查该地址对应的省份城市区县	/law_api/s1_b/get_address_info	query_conds: dict need_fields: list	AddrInfo	{"query_conds": {"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}, "need_fields": []}
def get_address_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_address_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_address_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_address_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_address_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_address_info called, hit, args={data}, rsp={rsp}")
        return rsp


#12	根据省市区查询区划代码	/law_api/s1_b/get_address_code	query_conds: dict need_fields: list	AddrCode	{"query_conds": {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}, "need_fields": []}
def get_address_code(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_address_code query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_address_code"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_address_code exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_address_code called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_address_code called, hit, args={data}, rsp={rsp}")
        return rsp

#13	根据日期及省份城市查询天气相关信息	/law_api/s1_b/get_temp_info	query_conds: dict need_fields: list	TempInfo	{"query_conds": {"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}, "need_fields": []}
def get_temp_info(*args, **kwargs):
    query_cond = {}
    if len(args) == 1 and type(args[0]) == dict:
        #using dict as query_cond
        query_cond = args[0]
    elif len(kwargs) > 0:
        #using kwargs as query_cond
        query_cond = kwargs
    else:
        raise ValueError(f"error get_temp_info query params: {args} {kwargs}")
    
    url = f"https://{domain}/law_api/s1_b/get_temp_info"
    data = {"query_conds": query_cond, "need_fields": []}
    
    try:
        raw_rsp = requests.post(url, json=data, headers=headers)
        rsp = raw_rsp.json()
        assert type(rsp) == list or type(rsp) == dict, f'调用参数错误:{raw_rsp.text}'
    except Exception as ex:
        logger.warn(f"get_temp_info exception, args={data}, rawargs={args, kwargs}, raw_rsp={raw_rsp.text} ex={ex}")
        raise ex
    
    if type(rsp) == list:
        logger.info(f"get_temp_info called, not found, args={data}, rsp={rsp}")
        print("##没查询到数据"); raise ValueError(f"{inspect.stack()[0][3]}没查询到数据 {query_cond}")
    else:
        logger.info(f"get_temp_info called, hit, args={data}, rsp={rsp}")
        return rsp


#-1 
def get_api_call_cnt(depth_kv_refers):
    #几种, 几次(最少)
    #串行几种，几次(最少)
    dedup = set()
    seq = []
    for di, depth in enumerate(depth_kv_refers): #depth
        for iters in depth: #codeact iters
            for call in iters: #calls in one run
                if not call[0].startswith('get_'): continue
                call_tuple = tuple([call[0]] + call[1])
                if call_tuple not in dedup:
                    dedup.add(call_tuple)
                    seq.append([di, call_tuple])
     
    kind_all = len({x[0] for x in dedup})
    cnt_all = len(seq)
    res_all = f"总共最少调用API共计:{kind_all}种, 次数{cnt_all}次"

    used_depth = set() #different depth, #different args
    used_args = set()
    used_funcs = set()
    seq_path = []
    for di, call_tuple in seq:
        func = call_tuple[0]
        args = call_tuple[1:]
        if di in used_depth: continue
        if func in used_funcs: continue
        if args in used_args: continue
        used_depth.add(di)
        used_funcs.add(func)
        used_args.add(args)
        seq_path.append([di, call_tuple])

    res_seq = f"。串行调用API共计:{len(used_funcs) - 1}种, 次数{len(seq_path) -1}次"

    return res_all + res_seq, seq