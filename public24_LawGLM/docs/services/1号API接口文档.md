## 1 号API接口函数 根据公司简称，获得该公司对应的基本信息

``` 
def get_company_info_service_by_abbreviation(company_abbreviation:  Annotated[str, "公司简称", True],need_fields: Annotated[str, "需要返回的字段列表 例如 [公司名称, 公司代码, 主营业务]", True]):
    """
   	根据公司简称，获得该公司对应的基本信息。
    """
    need_fields = keywords_parser(need_fields)
    rsp = get_company_info(query_conds={"公司简称": company_abbreviation},need_fields=need_fields)
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str
``` 

### 例子： 
### 1
##### 输入
``` 
company_abbreviation="安利股份",need_fields=[]
``` 
#### 输出 
``` 
{"公司名称": "安徽安利材料科技股份有限公司", "公司简称": "安利股份", "英文名称": "Anhui Anli Material Technology Co., Ltd.", "关联证券": "", "公司代码": "300218", "曾用简称": "", "所属市场": "深交所创业板", "所属行业": "橡胶和塑料制品业", "成立日期": "1994-07-12", "上市日期": "2011-05-18", "法人代表": "姚和平", "总经理": "姚和平", "董秘": "刘松霞", "邮政编码": "230093", "注册地址": "安徽省合肥市经济技术开发区桃花工业园拓展区（繁华大道与创新大道交叉口）", "办公地址": "XXX"}

```
### 2
#### 输入

company_abbreviation="海天精工",need_fields=[]
``` 
输出
{"公司名称": "宁波海天精工股份有限公司", "公司简称": "海天精工", "英文名称": "Ningbo Haitian Precision Machinery Co., Ltd.", "关联证券": "", "公司代码": "601882", "曾用简称": "", "所属市场": "上交所", "所属行业": "通用设备制造业", "成立日期": "2002-04-10", "上市日期": "2016-11-07", "法人代表": "张静章", "总经理": "王焕卫", "董秘": "谢精斌", "邮政编码": "315800", "注册地址": "浙江省宁波市北仑区黄山西路235号", "办公地址": "浙江省宁波市北仑区黄山西路235号", "联系电话": "0574-86188839", "传真": "0574-86182747", "官方网址": "www.haitianprecision.com", "电子邮箱": "jgzq@mail.haitian.com", "入选指数": "国证2000,国证Ａ指,上证380", "主营业务": "XXX"}
``` 


### 3
#### 输入
``` 
company_abbreviation="天通股份",need_fields=['公司代码','公司名称']
``` 

#### 输出
``` 
{"公司代码": "600330", "公司名称": "天通控股股份有限公司"}
``` 
