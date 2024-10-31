###  上市公司基本信息表
class CompanyInfo(Base):
    '''上市公司基本信息表'''
    __tablename__ = "company_info"
    公司名称 = Column(Text, primary_key=True, default='江西金达莱环保股份有限公司')
    公司简称 = Column(Text, default='金达莱')
    英文名称 = Column(Text, default='Jiangxi JDL Environmental Protection Co., Ltd.')
    公司代码 = Column(Text, default='688057')

###  公司工商照面信息表
class CompanyRegister(Base):
    '''公司工商照面信息表'''
    __tablename__ = 'company_register'
    公司名称 = Column(Text, primary_key=True, default='中山华利实业集团股份有限公司')
    统一社会信用代码 = Column(Text, default='914420007665649509')

### 上市公司投资子公司关联信息表
class SubCompanyInfo(Base):
    '''上市公司投资子公司关联信息表'''
    __tablename__ = 'sub_company_info'
    母公司全称 = Column(Text, default='马应龙药业集团股份有限公司')
    子公司名称 = Column(Text, primary_key=True, default='马应龙大健康有限公司')
    
### 法律文书信息表
class LegalDoc(Base):
    '''法律文书信息表'''
    __tablename__ = 'legal_doc'
    关联公司 = Column(Text, default='北京淳中科技股份有限公司')
    案号 = Column(Text, default='	(2020)陕0113民初19397号', primary_key=True)
    原告律师事务所 = Column(Text, default='陕西同州律师事务所')
    被告律师事务所 = Column(Text, default='北京风展律师事务所')


### 法院基础信息表（名录）
class CourtInfo(Base):
    '''法院基础信息表（名录）'''
    __tablename__ = 'court_info'
    法院名称 = Column(Text, default='安徽省高级人民法院', primary_key=True)
### 法院地址信息、代字表
class CourtCode(Base):
    '''法院地址信息、代字表'''
    __tablename__ = 'court_code'
    法院名称 = Column(Text, default='江苏省高级人民法院', primary_key=True)

### 律师事务所基础信息表（名录）
class LawfirmInfo(Base):
    '''律师事务所基础信息表（名录）'''
    __tablename__ = 'lawfirm_info'
    律师事务所名称 = Column(Text, default='上海东方华银律师事务所', primary_key=True)

### 律师事务所业务数据表
class LawfirmLog(Base):
    '''律师事务所业务数据表'''
    __tablename__ = 'lawfirm_log'
    律师事务所名称 = Column(Text, default='北京市金杜律师事务所', primary_key=True)
### 通用地址省市区信息表
class AddrInfo(Base):
    '''通用地址省市区信息表'''
    __tablename__ = 'addr_info'
    地址 = Column(Text, default='西藏自治区那曲地区安多县帕那镇中路13号', primary_key=True)
    省份 = Column(Text, default='西藏自治区')
    城市 = Column(Text, default='那曲市')
    区县 = Column(Text, default='安多县')
### 通用地址编码表
class AddrCode(Base):、
    '''通用地址编码表'''
    __tablename__ = 'addr_code'
    省份 = Column(Text, default='西藏自治区')
    城市 = Column(Text, default='拉萨市')
    城市区划代码 = Column(Text, default='540100000000')
    区县 = Column(Text, default='城关区')
    区县区划代码 = Column(Text, default='540102000000', primary_key=True)
### 天气数据表
class TempInfo(Base):
    '''天气数据表'''
    __tablename__ = 'temp_info'
    日期 = Column(Text, default='2019年12月11日', primary_key=True)
    省份 = Column(Text, default='四川省', primary_key=True)
    城市 = Column(Text, default='成都市')
    天气 = Column(Text, default='晴')
    最高温度 = Column(Text, default='16')
    最低温度 = Column(Text, default='1')
    湿度 = Column(Text, default='55')
### 法律文书摘要表
class LegalAbstract(Base):
    '''法律文书摘要表'''
    __tablename__ = 'legal_abstract'
    文件名 = Column(Text, default='（2019）沪0115民初61975号.txt')
    案号 = Column(Text, default='（2019）沪0115民初61975号', primary_key=True)
    文本摘要 = Column(Text, default='原告上海爱斯达克汽车空调系统有限公司与被告上海逸测检测技术服务有限公司因服务合同纠纷一案，原...')
### 限制高消费信息表
class XzgxfInfo(Base):
    '''限制高消费信息表'''
    __tablename__ = 'xzgxf_info'
    限制高消费企业名称 = Column(Text, default='枣庄西能新远大天然气利用有限公司')
    案号 = Column(Text, default='（2018）鲁0403执1281号', primary_key=True)
    执行法院 = Column(Text, default='山东省枣庄市薛城区人民法院')

```