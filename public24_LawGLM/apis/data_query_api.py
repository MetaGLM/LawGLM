from typing import Any, List, Union
from venv import logger
import requests
import json 


DOMAIN = "comm.chatglm.cn"
TEAM_TOKEN = "black_myth_wukong"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {TEAM_TOKEN}'
}


def get_company_info(query_conds: dict, need_fields: List[str] = []) -> dict:
    """
    根据上市公司名称、简称或代码查找上市公司信息。
    
    参数:
    query_conds -- 查询条件字典，例如{"公司名称": "上海妙可蓝多食品科技股份有限公司"}
    need_fields -- 需要返回的字段列表，例如["公司名称", "公司代码", "主营业务"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    
    例如：
        输入：
        {"公司名称": "上海妙可蓝多食品科技股份有限公司"}
        输出：
        {'公司名称': '上海妙可蓝多食品科技股份有限公司',
         '公司简称': '妙可蓝多',
         '英文名称': 'Shanghai Milkground Food Tech Co., Ltd.',
         '关联证券': '',
         '公司代码': '600882',
         '曾用简称': '大成股份>> *ST大成>> 华联矿业>> 广泽股份',
         '所属市场': '上交所',
         '所属行业': '食品制造业',
         '成立日期': '1988-11-29',
         '上市日期': '1995-12-06',
         '法人代表': '柴琇',
         '总经理': '柴琇',
         '董秘': '谢毅',
         '邮政编码': '200136',
         '注册地址': '上海市奉贤区工业路899号8幢',
         '办公地址': '上海市浦东新区金桥路1398号金台大厦10楼',
         '联系电话': '021-50188700',
         '传真': '021-50188918',
         '官方网址': 'www.milkground.cn',
         '电子邮箱': 'ir@milkland.com.cn',
         '入选指数': '国证Ａ指,巨潮小盘',
         '主营业务': '以奶酪、液态奶为核心的特色乳制品的研发、生产和销售，同时公司也从事以奶粉、黄油为主的乳制品贸易业务。',
         '经营范围': '许可项目：食品经营；食品互联网销售；互联网直播服务（不含新闻信息服务、网络表演、网络视听节目）；互联网信息服务；进出口代理。（依法须经批准的项目，经相关部门批准后方可开展经营活动，具体经营项目以相关部门批准文件或许可证件为准）。一般项目：乳制品生产技术领域内的技术开发、技术咨询、技术服务、技术转让；互联网销售（除销售需要许可的商品）；互联网数据服务；信息系统集成服务；软件开发；玩具销售。（除依法须经批准的项目外，凭营业执照依法自主开展经营活动）',
         '机构简介': '公司是1988年11月10日经山东省体改委鲁体改生字(1988)第56号文批准，由山东农药厂发起，采取社会募集方式组建的以公有股份为主体的股份制企业。1988年12月15日,经中国人民银行淄博市分行以淄银字(1988)230号文批准，公开发行股票。 1988年12月经淄博市工商行政管理局批准正式成立山东农药工业股份有限公司(营业执照:16410234)。',
         '每股面值': '1.0',
         '首发价格': '1.0',
         '首发募资净额': '4950.0',
         '首发主承销商': ''}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_info"

    data = {
        "query_conds":query_conds,
        "need_fields": need_fields
    }
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_company_register(query_conds: dict, need_fields: List[str] = []) -> dict:
    """
    根据公司名称，查询工商信息。

    参数:
    query_conds -- 查询条件字典，例如{"公司名称": "上海妙可蓝多食品科技股份有限公司"}
    need_fields -- 需要返回的字段列表，例如["公司名称", "公司代码", "主营业务"], need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    
    例如：
        输入：
        {"公司名称": "上海妙可蓝多食品科技股份有限公司"}
        输出：
        {'公司名称': '上海妙可蓝多食品科技股份有限公司',
         '登记状态': '存续',
         '统一社会信用代码': '91370000164102345T',
         '法定代表人': '柴琇', 
         '注册资本': '51379.1647', 
         '成立日期': '1988-11-29', 
         '企业地址': '上海市奉贤区工业路899号8幢', 
         '联系电话': '021-50185677', 
         '联系邮箱': 'pr@milkground.cn', 
         '注册号': '310000000165830', 
         '组织机构代码': '16410234-5', 
         '参保人数': '370', 
         '行业一级': '科学研究和技术服务业', 
         '行业二级': '科技推广和应用服务业', 
         '行业三级': '其他科技推广服务业', 
         '曾用名': '上海广泽食品科技股份有限公司,\n山东大成农药股份有限公司,\n山东农药工业股份有限公司', 
         '企业简介': '上海妙可蓝多食品科技股份有限公司（简称广泽股份，曾用名：上海广泽食品科技股份有限公司）始创于1998年，总部设在有“东方美谷”之称的上海市奉贤区，系上海证券交易所主板上市公司（证券代码600882）。广泽股份主要生产奶酪和液态奶两大系列产品，拥有“妙可蓝多”“广泽”“澳醇牧场”等国内知名品牌。公司分别在上海、天津、长春和吉林建有4间奶酪和液态奶加工厂，是国内领先的奶酪生产企业。秉承“成为满足国人需求的奶酪专家”的品牌理念，广泽股份一直致力于整合全球资源，为国人提供最好的奶酪产品。公司聘请了一批资深专家加盟，在上海、天津设立了研发中心，并与来自欧洲、澳洲的奶酪公司展开合作，引进了国际先进的生产设备和技术。为从根本上保证产品品质，公司在吉林省建有万头奶牛生态牧场，奶牛全部为进口自澳洲的荷斯坦奶牛，奶质已达欧盟标准。目前，公司可为餐饮和工业客户提供黄油、稀奶油、炼乳、车达和马苏里拉奶酪、奶油芝士、芝士片、芝士酱等产品系列，可直接为消费者提供棒棒奶酪、成长奶酪、三角奶酪、小粒奶酪、新鲜奶酪、慕斯奶酪和辫子奶酪、雪球奶酪等特色产品系列。多年来，广泽股份一直坚持“广纳百川，泽惠四海”的经营理念，恪守“以客户为中心，以奋斗者为本，诚信感恩，务实进取”的核心价值观，努力提高研发和生产技术，不断开发满足消费者需求的奶酪产品，成为深受消费者喜爱的乳品行业知名品牌。', 
         '经营范围': '许可项目：食品经营；食品互联网销售；互联网直播服务（不含新闻信息服务、网络表演、网络视听节目）；互联网信息服务；进出口代理。（依法须经批准的项目，经相关部门批准后方可开展经营活动，具体经营项目以相关部门批准文件或许可证件为准）一般项目：乳制品生产技术领域内的技术开发、技术咨询、技术服务、技术转让；互联网销售（除销售需要许可的商品）；互联网数据服务；信息系统集成服务；软件开发；玩具销售。（除依法须经批准的项目外，凭营业执照依法自主开展经营活动）'
         }
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_register"

    data = {
        "query_conds":query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_company_register_name(query_conds: dict,need_fields: List[str] = []) -> str:
    """
    根据统一社会信用代码查询公司名称。

    参数:
    query_conds -- 查询条件字典，例如{"统一社会信用代码": "913305007490121183"}
    need_fields -- 需要返回的字段列表，例如["公司名称", "公司代码", "主营业务"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    
    例如：
        输入：
        {"query_conds": {"统一社会信用代码": "913305007490121183"}}
        输出：
        {'公司名称': '天能电池集团股份有限公司'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_register_name"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()

def get_sub_company_info(query_conds: dict, need_fields: List[str] = []) -> dict:
    """
    根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息。

    参数:
    query_conds -- 查询条件字典，例如{"公司名称": "上海爱斯达克汽车空调系统有限公司"}
    need_fields -- 需要返回的字段列表，例如["关联上市公司全称","上市公司关系","上市公司参股比例","上市公司投资金额","公司名称],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段
    
    例如：
        输入：
        {"query_conds": {"公司名称": "上海爱斯达克汽车空调系统有限公司"}}
        输出：
        {'关联上市公司全称': '上海航天汽车机电股份有限公司', '上市公司关系': '子公司', '上市公司参股比例': '87.5', '上市公司投资金额': '8.54亿', '公司名称': '上海爱斯达克汽车空调系统有限公司'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_sub_company_info"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()

def get_listed_sub_company_info(query_conds: dict,need_fields: List[str] = []) -> List:
    """
    根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list。

    参数:
    query_conds -- 查询条件字典，例如{"关联上市公司全称": "上海航天汽车机电股份有限公司"}
    need_fields -- 需要返回的字段列表，例如["关联上市公司全称", "上市公司关系", "上市公司参股比例","上市公司投资金额","公司名称"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"关联上市公司全称": "上海航天汽车机电股份有限公司"}
        输出：
        [{'关联上市公司全称': '上海航天汽车机电股份有限公司', 
        '上市公司关系': '子公司', 
        '上市公司参股比例': '100.0', 
        '上市公司投资金额': '8800.00万', 
        '公司名称': '甘肃神舟光伏电力有限公司'}, 
        {'关联上市公司全称': '上海航天汽车机电股份有限公司', 
        '上市公司关系': '子公司', 
        '上市公司参股比例': '100.0', 
        '上市公司投资金额': '1.19亿', 
        '公司名称': '甘肃张掖神舟光伏电力有限公司'}]
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_sub_company_info_list"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_legal_document(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据案号查询裁判文书相关信息。

    参数:
    query_conds -- 查询条件字典，例如{"案号": "(2019)沪0115民初61975号"}
    need_fields -- 需要返回的字段列表，例如["关联公司", "标题", "案号","原告","被告","原告律师事务所","被告律师事务所","案由","涉案金额","判决结果","日期","文件名"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"案号": "(2019)沪0115民初61975号"}
        输出：
        {'关联公司': '上海爱斯达克汽车空调系统有限公司', 
        '标题': '上海爱斯达克汽车空调系统有限公司与上海逸测检测技术服务有限公司服务合同纠纷一审民事判决书', 
        '案号': '(2019)沪0115民初61975号', '文书类型': '民事判决书', 
        '原告': '上海爱斯达克汽车空调系统有限公司', 
        '被告': '上海逸测检测技术服务有限公司', 
        '原告律师事务所': '', 
        '被告律师事务所': '上海世韬律师事务所', 
        '案由': '服务合同纠纷', 
        '涉案金额': '1254802.58', 
        '判决结果': '一、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司测试费1,254,802.58元; \\n \\n二、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司违约金71,399.68元 。  \\n \\n负有金钱给付义务的当事人如未按本判决指定的期间履行给付金钱义务,应当依照《中华人民共和国民事诉讼法》第二百五十三条之规定,加倍支付迟延履行期间的债务利息 。  \\n \\n案件受理费16,736元,减半收取计8,368元,由被告上海逸测检测技术服务有限公司负担 。  \\n \\n如不服本判决,可在判决书送达之日起十五日内向本院递交上诉状,并按对方当事人的人数提出副本,上诉于上海市第一中级人民法院 。 ', 
        '日期': '2019-12-09 00:00:00', 
        '文件名': '（2019）沪0115民初61975号.txt'}
    """
    case_num = query_conds['案号']
    if isinstance(case_num, str):
        case_num = case_num.replace('（', '(').replace('）', ')')

    if isinstance(case_num, list):
        new_case_num = []
        for ele in case_num:
            new_case_num.append(ele.replace('（', '(').replace('）', ')'))
        case_num = new_case_num

    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_document"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }
    
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()


def get_legal_document_list(query_conds: dict,need_fields: List[str] = []) -> List:
    """
    根据涉案关联公司查询所有裁判文书相关信息list。

    参数:
    query_conds -- 查询条件字典，例如{"关联公司": "上海爱斯达克汽车空调系统有限公司"}
    need_fields -- 需要返回的字段列表，例如["关联公司", "标题", "案号","文书类型","原告","被告","原告律师事务所","被告律师事务所","案由","涉案金额","判决结果","日期","文件名"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"关联公司": "上海爱斯达克汽车空调系统有限公司"}
        输出：
        [{'关联公司': '上海爱斯达克汽车空调系统有限公司', 
        '标题': '上海爱斯达克汽车空调系统有限公司与上海逸测检测技术服务有限公司服务合同纠纷一审民事判决书', 
        '案号': '(2019)沪0115民初61975号', 
        '文书类型': '民事判决书', 
        '原告': '上海爱斯达克汽车空调系统有限公司', 
        '被告': '上海逸测检测技术服务有限公司', 
        '原告律师事务所': '', 
        '被告律师事务所': '上海世韬律师事务所', 
        '案由': '服务合同纠纷', 
        '涉案金额': '1254802.58', 
        '判决结果': '一、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司测试费1,254,802.58元; \\n \\n二、被告上海逸测检测技术服务有限公司应于本判决生效之日起十日内支付原告上海爱斯达克汽车空调系统有限公司违约金71,399.68元 。  \\n \\n负有金钱给付义务的当事人如未按本判决指定的期间履行给付金钱义务,应当依照《中华人民共和国民事诉讼法》第二百五十三条之规定,加倍支付迟延履行期间的债务利息 。  \\n \\n案件受理费16,736元,减半收取计8,368元,由被告上海逸测检测技术服务有限公司负担 。  \\n \\n如不服本判决,可在判决书送达之日起十五日内向本院递交上诉状,并按对方当事人的人数提出副本,上诉于上海市第一中级人民法院 。 ', 
        '日期': '2019-12-09 00:00:00', 
        '文件名': '（2019）沪0115民初61975号.txt'}]
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_document_list"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_court_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据法院名称查询法院名录相关信息。

    参数:
    query_conds -- 查询条件字典，例如{"法院名称": "上海市浦东新区人民法院"}
    need_fields -- 需要返回的字段列表，例如["法院名称", "法院负责人", "成立日期", "法院地址", "法院联系电话", "法院官网"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"法院名称": "上海市浦东新区人民法院"}
        输出：
        {'法院名称': '上海市浦东新区人民法院', 
        '法院负责人': '朱丹', 
        '成立日期': '2019-05-16', 
        '法院地址': '上海市浦东新区丁香路611号', 
        '法院联系电话': '-', 
        '法院官网': '-'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_court_info"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    print(rsp)
    return rsp.json()

def get_court_code(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据法院名称或者法院代字查询法院代字等相关数据。

    参数:
    query_conds -- 查询条件字典，例如{"法院名称": "上海市浦东新区人民法院"}
    need_fields -- 需要返回的字段列表，例如["法院名称","行政级别","法院级别","法院代字","区划代码","级别"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"法院名称": "上海市浦东新区人民法院"}
        输出：
        {'法院名称': '上海市浦东新区人民法院', 
        '行政级别': '市级', 
        '法院级别': '基层法院', 
        '法院代字': '沪0115', 
        '区划代码': '310115', 
        '级别': '1'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_court_code"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_lawfirm_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据律师事务所查询律师事务所名录。

    参数:
    query_conds -- 查询条件字典，例如{"律师事务所名称": "爱德律师事务所"}
    need_fields -- 需要返回的字段列表，例如["律师事务所名称", "律师事务所唯一编码", "律师事务所负责人", "事务所注册资本", "事务所成立日期", "律师事务所地址", "通讯电话", "通讯邮箱", "律所登记机关"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"律师事务所名称": "爱德律师事务所"}
        输出：
        {'律师事务所名称': '爱德律师事务所', 
        '律师事务所唯一编码': '31150000E370803331', 
        '律师事务所负责人': '巴布', 
        '事务所注册资本': '10万元人民币', 
        '事务所成立日期': '1995-03-14', 
        '律师事务所地址': '呼和浩特市赛罕区大学西街110号丰业大厦11楼', 
        '通讯电话': '0471-3396155', 
        '通讯邮箱': 'kehufuwubu@ardlaw.cn', 
        '律所登记机关': '内蒙古自治区呼和浩特市司法局'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_lawfirm_info"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_lawfirm_log(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据律师事务所查询律师事务所统计数据。

    参数:
    query_conds -- 查询条件字典，例如{"律师事务所名称": "北京市金杜律师事务所"}
    need_fields -- 需要返回的字段列表，例如["律师事务所名称","业务量排名","服务已上市公司","报告期间所服务上市公司违规事件","报告期所服务上市公司接受立案调查"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"律师事务所名称": "北京市金杜律师事务所"}
        输出：
        {'律师事务所名称': '北京市金杜律师事务所', 
        '业务量排名': '2', 
        '服务已上市公司': '68', 
        '报告期间所服务上市公司违规事件': '23', 
        '报告期所服务上市公司接受立案调查': '3'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_lawfirm_log"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_address_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据地址查该地址对应的省份城市区县。

    参数:
    query_conds -- 查询条件字典，例如{"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}
    need_fields -- 需要返回的字段列表，例如["地址","省份","城市","区县"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"地址": "西藏自治区那曲地区安多县帕那镇中路13号"}
        输出：
        {'地址': '西藏自治区那曲地区安多县帕那镇中路13号', 
        '省份': '西藏自治区', 
        '城市': '那曲市', 
        '区县': '安多县'}

    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_address_info"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_address_code(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据省市区查询区划代码。

    参数:
    query_conds -- 查询条件字典，例如{"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}
    need_fields -- 需要返回的字段列表，例如["省份","城市","区县","城市区划代码","区县区划代码"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"省份": "西藏自治区", "城市": "拉萨市", "区县": "城关区"}
        输出：
        {'省份': '西藏自治区', 
        '城市': '拉萨市', 
        '城市区划代码': '540100000000', 
        '区县': '城关区', 
        '区县区划代码': '540102000000'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_address_code"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_temp_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据日期及省份城市查询天气相关信息。

    参数:
    query_conds -- 查询条件字典，例如{"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}
    need_fields -- 需要返回的字段列表，例如["日期","省份","城市","天气","最高温度","最低温度","湿度"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"省份": "北京市", "城市": "北京市", "日期": "2020年1月1日"}
        输出：
        {'日期': '2020年1月1日', 
        '省份': '北京市', 
        '城市': '北京市', 
        '天气': '晴', 
        '最高温度': '11', 
        '最低温度': '1', 
        '湿度': '55'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_temp_info"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_legal_abstract(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据案号查询文本摘要。

    参数:
    query_conds -- 查询条件字典，例如{"案号": "（2019）沪0115民初61975号"}
    need_fields -- 需要返回的字段列表，例如["文件名","案号","文本摘要"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"案号": "（2019）沪0115民初61975号"}
        输出：
        {'文件名': '（2019）沪0115民初61975号.txt',
        '案号': '（2019）沪0115民初61975号',
        '文本摘要': '原告上海爱斯达克汽车空调系统有限公司与被告上海逸测检测技术服务有限公司因服务合同纠纷一案，原告请求被告支付检测费1,254,802.58元、延迟履行违约金71,399.68元及诉讼费用。被告辩称，系争合同已终止，欠款金额应为499,908元，且不认可违约金。\n法院认为，原告与腾双公司签订的测试合同适用于原被告，原告提供的测试服务应得到被告支付。依照《中华人民共和国合同法》第六十条、第一百零九条,《中华人民共和国民事诉讼法》第六十四条第一款,《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第九十条之规定判决被告支付原告检测费1,254,802.58元及违约金71,399.68元。'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_legal_abstract"
    case_num = query_conds['案号']
    if isinstance(case_num, str):
        case_num = case_num.replace('（', '(').replace('）', ')')

    if isinstance(case_num, list):
        new_case_num = []
        for ele in case_num:
            new_case_num.append(ele.replace('（', '(').replace('）', ')'))
        case_num = new_case_num
    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_xzgxf_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据案号查询限制高消费相关信息。

    参数:
    query_conds -- 查询条件字典，例如{"案号": "（2018）鲁0403执1281号"}
    need_fields -- 需要返回的字段列表，例如["限制高消费企业名称","案号","法定代表人","申请人","涉案金额","执行法院","立案日期","限高发布日期"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"案号": "（2018）鲁0403执1281号"}
        输出：
        {'限制高消费企业名称': '枣庄西能新远大天然气利用有限公司',
        '案号': '（2018）鲁0403执1281号',
        '法定代表人': '高士其',
        '申请人': '枣庄市人力资源和社会保障局',
        '涉案金额': '12000',
        '执行法院': '山东省枣庄市薛城区人民法院',
        '立案日期': '2018-11-16 00:00:00',
        '限高发布日期': '2019-02-13 00:00:00'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info"
    case_num = query_conds['案号']
    if isinstance(case_num, str):
        case_num = case_num.replace('（', '(').replace('）', ')')

    if isinstance(case_num, list):
        new_case_num = []
        for ele in case_num:
            new_case_num.append(ele.replace('（', '(').replace('）', ')'))
        case_num = new_case_num
    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_xzgxf_info_list(query_conds: dict,need_fields: List[str] = []) -> List:
    """
    根据企业名称查询所有限制高消费相关信息list。

    参数:
    query_conds -- 查询条件字典，例如{"限制高消费企业名称": "欣水源生态环境科技有限公司"}
    need_fields -- 需要返回的字段列表，例如["限制高消费企业名称","案号","法定代表人","申请人","涉案金额","执行法院","立案日期","限高发布日期"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"限制高消费企业名称": "欣水源生态环境科技有限公司"}
        输出：
        {'限制高消费企业名称': '欣水源生态环境科技有限公司',
        '案号': '（2023）黔2731执恢130号',
        '法定代表人': '刘福云',
        '申请人': '四川省裕锦建设工程有限公司惠水分公司',
        '涉案金额': '7500000',
        '执行法院': '贵州省黔南布依族苗族自治州惠水县人民法院',
        '立案日期': '2023-08-04 00:00:00',
        '限高发布日期': '2023-11-09 00:00:00'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info_list"
    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

def get_sum(nums: Union[List[float], List[str], List[int]]):
    """
    求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿，如"1万"
    """
    if not isinstance(nums, list) or len(nums) == 0:
        return -100
    
    if any(not isinstance(x, (int, float, str)) for x in nums):
        return -100
    
    def map_str_to_num(str_num):
        try:
            str_num = str_num.replace("千", "*1e3")
            str_num = str_num.replace("万", "*1e4")
            str_num = str_num.replace("亿", "*1e8")
            return eval(str_num)
        except Exception as e:
            logger.error(e)
            pass
        return -100
    
    if isinstance(nums[0], str):
        nums = [map_str_to_num(i) for i in nums]
    
    try:
        return sum(nums)
    except Exception as e:
        logger.error(e)
    
    return -100

def rank(keys: List[Any], values: List[float], is_desc: bool = False):
    '''
    排序接口，返回按照values排序的keys
    '''
    return [i[0] for i in sorted(zip(keys, values), key=lambda x: x[1], reverse=is_desc)]

# def save_dict_list_to_word(company_name: str, dict_list: str):
#     """
#    通过传入结构化信息，制作生成公司数据报告（demo）。
#     """
#     url = f"https://{DOMAIN}/law_api/s1_b/save_dict_list_to_word"
#     data = {
#         'company_name': company_name,
#         'dict_list': dict_list.replace("{{","{").replace("}}","}")
#     }
#     try: 
#         rsp = requests.post(url, json=data, headers=headers)
#         open(f"{company_name}.docx", "wb").write(rsp.content)
#     except Exception as e:
#         logger.error(e)
#         return {}
#     return {"file_name": f"{company_name}.docx"}

def save_dict_list_to_word(company_name: str, dict_list: str):
    """
   通过传入结构化信息，制作生成公司数据报告（demo）。
    """
    url = f"https://{DOMAIN}/law_api/s1_b/save_dict_list_to_word"
    data = {
        'company_name': company_name,
        'dict_list': dict_list.replace("{{","{").replace("}}","}")
    }
    rsp = requests.post(url, json=data, headers=headers)
    return rsp.content



def get_citizens_sue_citizens(query_conds: dict):
    """
   民事起诉状(公民起诉公民)。
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_citizens_sue_citizens"
    data = query_conds

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()

def get_company_sue_citizens(query_conds: dict):
    """
   	民事起诉状(公司起诉公民)。
    """
    # print(query_conds)
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_sue_citizens"
    data = query_conds
    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()

def get_citizens_sue_company(query_conds: dict):
    """
   	民事起诉状(公民起诉公司)。
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_citizens_sue_company"
    data = query_conds

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()

def get_company_sue_company(query_conds: dict):
    """
   	民事起诉状(公司起诉公司)。
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_sue_company"
    data = query_conds

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()


