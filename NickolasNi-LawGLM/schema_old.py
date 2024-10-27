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
    成立日期: str
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
    首发价: str
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
    关联上市公司股票代码: str
    关联上市公司股票简称: str
    关联上市公司全称: str
    上市公司关系: str
    上市公司参股比例: str
    上市公司投资金额: str
    公司名称: str  # 子公司的公司名称


class LegalDocument(BaseModel):
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


def build_enum_class(dataclass, exclude_enums=[]):
    keys = [key for key in dataclass.__fields__.keys() if key not in exclude_enums]
    return Enum(dataclass.__name__ + "Enum", dict(zip(keys, keys)))


CompanyInfoEnum = build_enum_class(CompanyInfo, exclude_enums=["公司名称"])
CompanyRegisterEnum = build_enum_class(CompanyRegister, exclude_enums=["公司名称"])
SubCompanyInfoEnum = build_enum_class(SubCompanyInfo, exclude_enums=["公司名称"])
LegalDocumentEnum = build_enum_class(LegalDocument, exclude_enums=["案号"])

keys = ["公司名称", "公司代码"]
CompanyNameCodeEnum = Enum("CompanyNameCodeEnum", dict(zip(keys, keys)))


def build_enum_list(enum_class):
    return [enum.value for enum in enum_class]


database_schema = f"""
公司基础信息表（CompanyInfo）有下列字段：
{build_enum_list(CompanyInfoEnum)}
-------------------------------------

公司注册信息表（CompanyRegister）有下列字段：
{build_enum_list(CompanyRegisterEnum)}
-------------------------------------

公司子公司融资信息表（SubCompanyInfo）有下列字段：
{build_enum_list(SubCompanyInfoEnum)}
-------------------------------------

法律文书表（LegalDocument）有下列字段：
{build_enum_list(LegalDocumentEnum)}
-------------------------------------
"""
