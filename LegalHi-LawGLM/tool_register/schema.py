from pydantic import BaseModel, Field
from enum import Enum


class CompanyInfo(BaseModel):
    公司名称: str
    公司简称: str
    英文名称: str
    关联证券: str
    公司代码: str
    曾用简称: str
    所属市场: str
    所属行业: str
    上市日期: str
    法人代表: str
    总经理: str
    董秘: str
    邮政编码: str
    注册地址: str
    办公地址: str
    联系电话: str
    传真: str
    官方网址: str
    电子邮箱: str
    入选指数: str
    主营业务: str
    经营范围: str
    机构简介: str
    每股面值: str
    首发价格: str
    首发募资净额: str
    首发主承销商: str


class CompanyRegister(BaseModel):
    公司名称: str
    登记状态: str
    统一社会信用代码: str
    法定代表人: str
    注册资本: str
    成立日期: str
    企业地址: str
    联系电话: str
    联系邮箱: str
    注册号: str
    组织机构代码: str
    参保人数: str
    行业一级: str
    行业二级: str
    行业三级: str
    曾用名: str
    企业简介: str
    经营范围: str


class SubCompanyInfo(BaseModel):
    关联上市公司全称: str
    上市公司关系: str
    上市公司参股比例: str
    上市公司投资金额: str
    公司名称: str


class LegalDoc(BaseModel):
    关联公司: str
    标题: str
    案号: str
    文书类型: str
    原告: str
    被告: str
    原告律师事务所: str
    被告律师事务所: str
    案由: str
    涉案金额: str
    判决结果: str
    日期: str
    文件名: str


class CourtInfo(BaseModel):
    法院名称: str
    法院负责人: str
    成立日期: str
    法院地址: str
    法院联系电话: str
    法院官网: str


class CourtCode(BaseModel):
    法院名称: str
    行政级别: str
    法院级别: str
    法院代字: str
    区划代码: str
    级别: str


class LawfirmInfo(BaseModel):
    律师事务所名称: str
    律师事务所唯一编码: str
    律师事务所负责人: str
    事务所注册资本: str
    事务所成立日期: str
    律师事务所地址: str
    通讯电话: str
    通讯邮箱: str
    律所登记机关: str


class LawfirmLog(BaseModel):
    律师事务所名称: str
    业务量排名: str
    服务已上市公司: str
    报告期间所服务上市公司违规事件: str
    报告期所服务上市公司接受立案调查: str


class AddrInfo(BaseModel):
    地址: str
    省份: str
    城市: str
    区县: str


class AddrCode(BaseModel):
    省份: str
    城市: str
    城市区划代码: str
    区县: str
    区县区划代码: str


class TempInfo(BaseModel):
    日期: str
    省份: str
    城市: str
    天气: str
    最高温度: str
    最低温度: str
    湿度: str


class LegalAbstract(BaseModel):
    文件名: str
    案号: str
    文本摘要: str


class XzgxfInfo(BaseModel):
    限制高消费企业名称: str
    案号: str
    法定代表人: str
    申请人: str
    涉案金额: str
    执行法院: str
    立案日期: str
    限高发布日期: str


def build_enum_class(dataclass, exclude_enums=[]):
    keys = [str(key) for key in dataclass.__fields__.keys() if key not in exclude_enums]
    return Enum(dataclass.__name__ + "Enum", dict(zip(keys, keys)))


CompanyInfoEnum = build_enum_class(CompanyInfo)
CompanyRegisterEnum = build_enum_class(CompanyRegister)
SubCompanyInfoEnum = build_enum_class(SubCompanyInfo)
LegalDocEnum = build_enum_class(LegalDoc)
CourtInfoEnum = build_enum_class(CourtInfo)
CourtCodeEnum = build_enum_class(CourtCode)
LawfirmInfoEnum = build_enum_class(LawfirmInfo)
LawfirmLogEnum = build_enum_class(LawfirmLog)
AddrInfoEnum = build_enum_class(AddrInfo)
AddrCodeEnum = build_enum_class(AddrCode)
TempInfoEnum = build_enum_class(TempInfo)
LegalAbstractEnum = build_enum_class(LegalAbstract)
XzgxfInfoEnum = build_enum_class(XzgxfInfo)


def build_enum_list(enum_class):
    return [enum.value for enum in enum_class]


database_schema = f"""
CompanyInfo有下列字段：
{build_enum_list(CompanyInfoEnum)}
-------------------------------------
CompanyRegister有下列字段：
{build_enum_list(CompanyRegisterEnum)}
-------------------------------------
SubCompanyInfo有下列字段：
{build_enum_list(SubCompanyInfoEnum)}
-------------------------------------
LegalDoc有下列字段：
{build_enum_list(LegalDocEnum)}
-------------------------------------
CourtInfo有下列字段：
{build_enum_list(CourtInfoEnum)}
-------------------------------------
CourtCode有下列字段：
{build_enum_list(CourtCodeEnum)}
-------------------------------------
LawfirmInfo有下列字段：
{build_enum_list(LawfirmInfoEnum)}
-------------------------------------
LawfirmLog有下列字段：
{build_enum_list(LawfirmLogEnum)}
-------------------------------------
AddrInfo有下列字段：
{build_enum_list(AddrInfoEnum)}
-------------------------------------
AddrCode有下列字段：
{build_enum_list(AddrCodeEnum)}
-------------------------------------
TempInfo有下列字段：
{build_enum_list(TempInfoEnum)}
-------------------------------------
LegalAbstract有下列字段：
{build_enum_list(LegalAbstractEnum)}
-------------------------------------
XzgxfInfo有下列字段：
{build_enum_list(XzgxfInfoEnum)}
-------------------------------------
"""
