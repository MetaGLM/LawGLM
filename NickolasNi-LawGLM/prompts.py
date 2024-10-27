TABLE_PROMPT_SEPARATE = """
根据数据表的属性，判断回答问题所需要的数据表。问题可能与其中的一张或者多张表有关。
请分析问题和表名以及表中字段的相关性，问题中涉及到任何表或者表中的字段都需要返回对应的表名。请尽可能多的返回相关表。
如果问题中涉及错别字等错误需要先修复再进行判断所用数据表。比如'玉门拓璞科技开发有限责任公司的地址在哪里？该公司被限告的涉案总额为？'其中的'被限告'应该改为'被限高'也就是限制高消费，对应到:xzgxf_info.

如果问题中涉及到子公司或母公司，那么上市公司投资子公司关联信息表与问题有关。
如问题中涉及公司时,比如问题中包含公司或者行业等，那么答案中要包含company_info和company_register。
如问题包含涉案信息、法律文书等,那么答案中要包含legal_doc.
当问题询问省份城市区县等地址信息时需要包含addr_info和addr_code.

Example :
----
问题：(2021)冀0207民初6756号的被告是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？
分析：(2021)冀0207民初6756号是字段'案号'该字段出现在表legal_doc、legal_abstract、xzgxf_info。字段'被告'出现在表legal_doc。'上市公司'和上市公司基本信息表相关。字段'股票代码'和'上市日期'出现在表company_info。字段'统一社会信用代码'出现在表company_register。
答案：{{"table_name": ["company_info","company_register","legal_doc","legal_abstract",,"xzgxf_info"]}}

问题：(2020)渝0112民初27463号的原告师事务所所在的城市区划代码是多少
分析：(2021)冀0207民初6756号是字段'案号'该字段出现在表legal_doc、legal_abstract、xzgxf_info。字段'原告'出现在表legal_doc。'律师事务所'和law_firm_info、law_firm_log相关。字段'城市区划代码'出现在表addr_code。
答案：{{"table_name": ["addr_code","law_firm_info","law_firm_log","legal_doc","legal_abstract",,"xzgxf_info"]}}

问题：(2021)豫0302知民初616号的原告是谁，它是哪个行业的
分析：(2021)冀0207民初6756号是字段'案号'该字段出现在表legal_doc、legal_abstract、xzgxf_info。'行业'和公司信息相关并且company_info表含有'所属行业'字段。
答案：{{"table_name": ["company_info","legal_doc","legal_abstract","xzgxf_info"]}}

问题：(2021)苏0481民初4582号的法院在哪个区县？
分析：逻辑链:通过案号(2021)苏0481民初4582号获得法院代字苏0481,用法院代字查到court_code中的法院名称,用法院名称查到court_info中的法院地址,用法院地址查到addr_info中的区县信息
答案：{{"table_name": ["court_code","court_info","addr_info"]}}
----

问题：{question}
----
table 1: {{
    table_name: company_info
    description: 上市公司基本信息表
    property: 公司名称, 公司简称, 英文名称, 关联证券, 公司代码_股票代码, 曾用简称, 所属市场, 所属行业, 成立日期, 上市日期, 法人代表, 总经理 ,董秘, 邮政编码, 注册地址, 办公地址, 联系电话, 传真, 官方网址, 电子邮箱, 入选指数, 主营业务, 经营范围, 机构简介, 每股面值, 首发价, 首发募资净额, 首发主承销商
    }}

table 2: {{
    table_name: company_register
    description: 公司工商照面信息表
    property: 公司名称, 登记状态, 统一社会信用代码, 法定代表人, 注册资本, 成立日期, 企业地址, 联系电话, 联系邮箱, 注册号, 组织机构代码, 参保人数, 行业一级, 行业二级, 行业三级, 曾用名, 企业简介,经营范围
    }}
    
table 3: {{
    table_name: sub_company_info
    description: 上市公司投资子公司关联信息表
    property: 关联上市公司全称, 上市公司关系, 上市公司参股比例, 上市公司投资金额, 公司名称
    }}

table 4: {{
    table_name: legal_doc
    description: 法律文书信息表
    property: 关联公司, 标题, 案号, 文书类型, 原告, 被告, 原告律师事务所, 被告律师事务所, 案由, 涉案金额, 判决结果, 日期, 文件名
    }}

table 5: {{
    table_name: court_info
    description: 法院基础信息表（名录）
    property: 法院名称, 法院负责人, 成立日期, 法院地址, 法院联系电话, 法院官网
    }}
    
table 6: {{
    table_name: court_code
    description: 法院地址信息、代字表
    property: 法院名称, 行政级别, 法院级别, 法院代字, 区划代码, 级别
    }}
    
table 7: {{
    table_name: law_firm_info
    description: 律师事务所信息表（名录）
    property: 律师事务所名称, 律师事务所唯一编码, 律师事务所负责人, 事务所注册资本, 事务所成立日期, 律师事务所地址, 通讯电话, 通讯邮箱, 律所登记机关
    }}
    
table 8: {{
    table_name: law_firm_log
    description: 律师事务所业务数据表
    property: 律师事务所名称, 业务量排名, 服务已上市公司, 报告期间所服务上市公司违规事件, 报告期所服务上市公司接受立案调查
    }}
    
table 9: {{
    table_name: addr_info
    description: 通用地址省市区信息表
    property: 地址, 省份, 城市, 区县
    }}
    
table 10: {{
    table_name: addr_code
    description: 通用地址编码表
    property: 省份, 城市, 城市区划代码, 区县, 区县区划代码
    }}
    
table 11: {{
    table_name: temp_info
    description: 天气数据表
    property: 日期, 省份, 城市, 天气, 最高温度, 最低温度, 湿度
    }}
    
table 12: {{
    table_name: legal_abstract
    description: 法律文书摘要表
    property: 文件名, 案号, 文本摘要
    }}
     
table 13: {{
    table_name: xzgxf_info
    description: 限制高消费数据表
    property: 限制高消费企业名称, 案号, 法定代表人, 申请人, 涉案金额, 执行法院, 立案日期, 限高发布日期
    }}
----
请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
数据表存放在数组中，如果问题和所有数据表都无关则返回空数组。
```json
{{
    "table_name": [""]
}}
``` 
"""


TABLE_PROMPT = """
根据数据表的属性，判断回答问题所需要的数据表。
----
table 1: {{
    名称: company_info
    属性值: 公司名称, 公司简称, 英文名称, 关联证券, 公司代码, 曾用简称, 所属市场, 所属行业, 上市日期, 法人代表, 总经理 ,董秘, 邮政编码, 注册地址, 办公地址, 联系电话, 传真, 官方网址, 电子邮箱, 入选指数, 主营业务, 经营范围, 机构简介, 每股面值, 首发价, 首发募资净额, 首发主承销商, 登记状态, 统一社会信用代码, 注册资本, 成立日期, 省份, 城市, 区县, 注册号, 组织机构代码, 参保人数, 企业类型, 曾用名
    }}

table 2: {{
    名称: sub_company_info
    属性值: 关联上市公司股票代码, 关联上市公司股票简称, 关联上市公司全称, 上市公司关系, 上市公司参股比例, 上市公司投资金额, 公司名称
    }}

table 3: {{
    名称: legal_document
    属性值: 标题, 案号, 文书类型, 原告, 被告, 原告律师, 被告律师, 案由, 审理法条依据, 涉案金额, 判决结果, 胜诉方, 文件名
}}
----
请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
数据表存放在数组中，如果问题和所有数据表都无关则返回空数组。
```json
{{
    "名称": [""]
}}
``` 
"""

QUESTION_CLASS = """
你是一个语言学专家,尤其擅长对文本进行分类。
一共有三类：
类1是文本中包含需要写起诉状的,起诉状一般是公司起诉公司,公司起诉法人,法人起诉公司,法人起诉法人这四种,文本也会包含起诉状所需的起诉双方,起诉原因,委托律所,法院和起诉时间等信息，文本明确要求把这些信息(不一定把这些所有信息全部纳入)纳入起诉状时才是类1。
类2是文本中包含需要写一份公司的整合报告,一般会要求把公司的工商信息、子公司信息、裁判文书和限制高消费纳入整合报告，文本明确要求把这些信息(不一定把这4种信息全部纳入,比如少了裁判文书或者限制高消费)纳入整合报告时才是类2。
类3是文本不包含前面两种需求的其他问题一般是通过接口查询一些公司、法院、案件、律师和天气等信息。需要注意类3的文本中有时候会包含'起诉状','整合报告'，但只是在称述用户要写起诉状或者整合报告，没有给出详细要求且没有给出纳入起诉状或者整合报告的必要信息，此时应该分类成类3。

请注意有些文本具有误导性.
比如文本："我是一家律师事务所的律师，我的委托人的子公司准备起诉一家上市公司，想要准备起诉书，我们已经查询过该公司工商信息中的法人及电话，电话打不通人名也对不上，请帮我查询一下该上市公司的法人信息及电话吧，该上市公司的全称为浙江海正药业股份有限公司。"
分析：虽然文本中包含了'想要准备起诉书'但包含起诉状所需要的信息如'起诉方'、'被起诉方'、'案号'、'法院'、'起诉时间'等，而真正的问题是后面的查询'该上市公司的法人信息及电话'，所以此文本是类3.

比如文本：“我是上海市第一人民法院的书记员法官，我要写一份关于重庆秦安机电股份有限公司的整合报告。请帮查询下这家公司的投资金额最高的子公司是？投资金额是？法定代表人、成立日期、统一社会信用代码分别是什么？”
分析：虽然文本中包含了'写一份关于重庆秦安机电股份有限公司的整合报告'但没有包含整合报告所需要的信息如'工商信息'、'子公司信息'、'裁判文书'和'限制高消费'，而真正的问题是后面的查询'重庆秦安机电股份有限公司的投资金额最高的子公司是？投资金额是？法定代表人、成立日期、统一社会信用代码分别是什么？'，所以此文本是类3。

比如文本:"请帮我查询安徽合力叉车销售有限公司涉案金额最高的法院的负责人是？我需要写整合报告"
分析：虽然文本中包含了'写整合报告'但没有包含整合报告所需要的信息如'工商信息'、'子公司信息'、'裁判文书'和'限制高消费'，而真正的问题是前面的查询'安徽合力叉车销售有限公司涉案金额最高的法院的负责人'所以此文本是类3。


请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：赛轮集团股份有限公司与晶瑞电子材料股份有限公司发生了买卖合同纠纷，赛轮集团股份有限公司委托给了安徽安康律师事务所，晶瑞电子材料股份有限公司委托给了安徽奥成律师事务所，请写一份民事起诉状给公安县人民法院时间是2024-01-01
```json
{{
    "category_name": "类1"
}}
``` 

example：甘肃省敦煌种业集团股份有限公司关于工商信息及子公司信息，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果）整合报告。
```json
{{
    "category_name": "类2"
}}
``` 

example：(2019)陕民申98号的被告是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？该公司是否被限制高消费？如果是被限制高消费的涉案金额总额为？请保留四位小数
```json
{{
    "category_name": "类3"
}}
``` 

example：我是一名律师，请写一份民事起诉状给青县人民法院时间是2024-02-02，南京康尼机电股份有限公司法人与江苏江南高纤股份有限公司发生了民事纠纷，南京康尼机电股份有限公司委托给了江西辰星律师事务所，江苏江南高纤股份有限公司委托给了江西心者律师事务所，注：法人的地址是上海市松江区莘松路108弄8号904室，电话是18041688830。
```json
{{
    "category_name": "类1"
}}
``` 

example：请问甘肃省敦煌种业集团股份有限公司的法人是谁，同时请写一份整合报告关于该公司的工商信息及子公司信息，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果）。
```json
{{
    "category_name": "类2"
}}
``` 

example：我是上海有应律师事务所的负责人，我要写一份针对上海远奕电子科技有限公司起诉书时缺少一些信息，请帮我查询一下该公司的公司代码、所属市场、所属行业分别为何?
```json
{{
    "category_name": "类3"
}}
``` 

example：我是一家律师事务所的律师，我的委托人的子公司准备起诉一家上市公司，想要准备起诉书，我们已经查询过该公司工商信息中的法人及电话，电话打不通人名也对不上，请帮我查询一下该上市公司的法人信息及电话吧，该上市公司的全称为浙江海正药业股份有限公司。
```json
{{
    "category_name": "类3"
}}
``` 

example：请帮我查询上海建工公司涉诉案件中涉案金额最高的案件中原告律师所来自哪个城市？我需要写整合报告
```json
{{
    "category_name": "类3"
}}
``` 

example：保定市天威西路2222号地址对应的省市区县分别是？
```json
{{
    "category_name": "类3"
}}
``` 

example：我是上海市第一人民法院的书记员法官，我要写一份关于重庆秦安机电股份有限公司的整合报告。请相关信息请帮我查询下：这家公司的投资金额最高的子公司是？投资金额是？法定代表人、成立日期、统一社会信用代码分别是什么？”
```json
{{
    "category_name": "类3"
}}
``` 

example：2021年8月19日这一天,这个地址的上海市闵行区新骏环路138号1幢401室的天气如何?其最高温度和最低温度分别是多少?然后在帮我查下这个地址的区县名称以及他的区县区划代码?
```json
{{
    "category_name": "类3"
}}
``` 

example：请帮我查询一下四方科技集团股份有限公司的法定代表人和统一社会代码分别是？本题调用了多少类API？
```json
{{
    "category_name": "类3"
}}
``` 

请对以下文本进行分类：
<文本内容>
{query}
</文本内容>"""

system_sue_prompt = """你是一位金融法律专家，你的任务是根据用户给出的query，提取其中的关键信息以便后续程序通过这些关键信息撰写起诉状。
需要解析出的字段如下:起诉状类别,原告单位,被告单位,原告律师事务所,被告律师事务所,诉讼请求,法院名称,起诉日期.
起诉状类别有以下可选:法人起诉法人,公司起诉法人,法人起诉公司,公司起诉公司，这4个可选.
其中的时间解析出的格式为XXXX年XX月XX日,几月几日如果是个位数需要在十位上加0，如：2020年4月3日须变成2020年04月03日。

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：深圳市佳士科技股份有限公司的法人与天津凯发电气股份有限公司的法人发生了产品生产者责任纠纷，深圳市佳士科技股份有限公司委托给了山东崇义律师事务所，天津凯发电气股份有限公司委托给了山东海金州律师事务所，请写一份民事起诉状给辽宁省沈阳市中级人民法院时间是2024-04-02，注：法人的地址电话可用公司的代替。
```json
{{
    "起诉状类别":"法人起诉法人",
    "原告单位":"深圳市佳士科技股份有限公司",
    "被告单位":"天津凯发电气股份有限公司",
    "原告律师事务所":"山东崇义律师事务所",
    "被告律师事务所":"山东海金州律师事务所",
    "诉讼请求":"产品生产者责任纠纷",
    "法院名称":"辽宁省沈阳市中级人民法院",
    "起诉日期":"2024年04月02日"
}}
``` 

example：湖南中科电气股份有限公司与上海硅产业集团股份有限公司的法人发生了建设工程分包合同纠纷，湖南中科电气股份有限公司委托给了辽宁瑾华律师事务所，上海硅产业集团股份有限公司委托给了辽宁天衡律师事务所，请写一份民事起诉状给山西省晋中市中级人民法院时间是2024-03-02，注：法人的地址电话可用公司的代替。
```json
{{
    "起诉状类别":"公司起诉法人",
    "原告单位":"湖南中科电气股份有限公司",
    "被告单位":"上海硅产业集团股份有限公司",
    "原告律师事务所":"辽宁瑾华律师事务所",
    "被告律师事务所":"辽宁天衡律师事务所",
    "诉讼请求":"建设工程分包合同纠纷",
    "法院名称":"山西省晋中市中级人民法院",
    "起诉日期":"2024年03月02日"
}}
``` 

example：南京康尼机电股份有限公司法人与江苏江南高纤股份有限公司发生了民事纠纷，南京康尼机电股份有限公司委托给了江西辰星律师事务所，江苏江南高纤股份有限公司委托给了江西心者律师事务所，请写一份民事起诉状给青县人民法院时间是2024-02-02，注：法人的地址电话可用公司的代替。
```json
{{
    "起诉状类别":"法人起诉公司",
    "原告单位":"南京康尼机电股份有限公司",
    "被告单位":"江苏江南高纤股份有限公司",
    "原告律师事务所":"江西辰星律师事务所",
    "被告律师事务所":"江西心者律师事务所",
    "诉讼请求":"民事纠纷",
    "法院名称":"青县人民法院",
    "起诉日期":"2024年02月02日"
}}
``` 

example：赛轮集团股份有限公司与晶瑞电子材料股份有限公司发生了买卖合同纠纷，赛轮集团股份有限公司委托给了安徽安康律师事务所，晶瑞电子材料股份有限公司委托给了安徽奥成律师事务所，请写一份民事起诉状给公安县人民法院时间是2024-01-01
```json
{{
    "起诉状类别":"公司起诉公司",
    "原告单位":"赛轮集团股份有限公司",
    "被告单位":"晶瑞电子材料股份有限公司",
    "原告律师事务所":"安徽安康律师事务所",
    "被告律师事务所":"安徽奥成律师事务所",
    "诉讼请求":"买卖合同纠纷",
    "法院名称":"公安县人民法院",
    "起诉日期":"2024年01月01日"
}}
``` 
"""

prompt_check_company_info_args = """请对用户输入的公司名称进行判断和修正。
错误类型包含但不限于：重复的叠字，错别字，多加了'省','市'：如'山东省戴瑞克新材料有限公司'应是'山东戴瑞克新材料有限公司'。
如果用户输入的公司信息正确则fixed_info的值就是用户输入的公司名称。

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙龙元建设集团股份有限公司
```json
{{"fixed_info":"龙元建设集团股份有限公司"}}
``` 

example：信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司
```json
{{"fixed_info":"信息产业电子第十一设计研究院科技工程股份有限公司"}}
``` 

example：河南龙马环境产业有有有有限限限限公公公公司司司司
```json
{{"fixed_info":"河南龙马环境产业有限公司"}}
``` 

example：温洲明鹿基础设施投资有限公司
```json
{{"fixed_info":"温州明鹿基础设施投资有限公司"}}
``` 

example：山东省戴瑞克新材料有限公司
```json
{{"fixed_info":"山东戴瑞克新材料有限公司"}}
``` 
"""


pre_check_company_name_prompt = """你是一位语义专家，尤其擅长修复语义错误。你的任务是根据用户输出的实例，返回修正后的实例。
用户的输入实例是公司名称,股票代码和统一社会信用代码这三种中的一种。
股票代码6位纯数字，统一社会信用代码由18位数字和字母组成。
错误类型包含但不限于：重复的叠字，错别字，多加了'省','市'。
如果用户输入的实例正确则fixed_info的值就是用户输入的公司名称。

example:
龙龙元建设集团股份有限公司,应改为:龙元建设集团股份有限公司
信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司,应改为:信息产业电子第十一设计研究院科技工程股份有限公司
陕西建设机械股份有限公公,应改为:陕西建设机械股份有限公司
河南龙马环境产业有有有有限限限限公公公公司司司司,应改为:河南龙马环境产业有限公司
温洲明鹿基础设施投资有限公司,应改为:温州明鹿基础设施投资有限公司
山东省戴瑞克新材料有限公司,应改为:山东戴瑞克新材料有限公司
330000116644,应改为:300164
330000667744,应改为:300674

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙龙元建设集团股份有限公司
```json
{{"fixed_info":"龙元建设集团股份有限公司"}}
``` 

example：信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司
```json
{{"fixed_info":"信息产业电子第十一设计研究院科技工程股份有限公司"}}
``` 

example：陕西建设机械股份有限公公
```json
{{"fixed_info":"陕西建设机械股份有限公司"}}
``` 

example：河南龙马环境产业有有有有限限限限公公公公司司司司
```json
{{"fixed_info":"河南龙马环境产业有限公司"}}
``` 

example：温洲明鹿基础设施投资有限公司
```json
{{"fixed_info":"温州明鹿基础设施投资有限公司"}}
``` 

example：山东省戴瑞克新材料有限公司
```json
{{"fixed_info":"山东戴瑞克新材料有限公司"}}
``` 

example：330000116644
```json
{{"fixed_info":"300164"}}
``` 

example：330000667744
```json
{{"fixed_info":"300674"}}
``` 
"""


suggested_logic_chain_prompt = """你是一个语言学和逻辑学专家。请根据问题和可用的API给出解答问题的逻辑链。
在完整这个任务时需要首先通读问题内容结合API,找出所有问题所需要的api和参数,再更基于API和所需参数，给出完整的逻辑链。总体思路是通过问题找出需要的API和参数，再看所需参数是否需要调用API获得如果是那么又需要什么API和其参数，这样通过问题一步一步往前推理找出所需信息。

比如问题：(2020)新2122民初1105号案件中，审理当天审理法院与原告的律师事务所所在城市的最低温度相差多少度？本题使用的API个数为？最小调用次数为多少次？
思路：这个问题主要问两个地方的最低温度,温度信息可以通过get_temp_info和参数省份,城市,日期。其中日期是审理当天,可以通过get_legal_document和问题中已知的案号找到字段日期。省份,城市需要通过get_address_info和审理法院与原告的律师事务所地址找到。
法院地址需要先通过案号中的法院代字和get_court_code先找出法院名称再用法院名称和get_court_info找出法院地址。
原告的律师事务所地址需要先通过get_legal_document和问题中已知的案号找出律师事务所名称再用律师事务所名称和get_lawfirm_info找出律师事务所地址。
请忽略问题中关于'API个数为?','最小调用次数为多少次'等这类api调用问题，只需要给出处理问题的逻辑链即可。
总结：
1. 通过案号找出案件中的原告律师事务所和日期
2. 通过案号中的法院代字找出法院名称
3. 通过法院名称找出法院地址
4. 通过法院地址找出省份, 城市信息
5. 通过法院的省份, 城市和1中的日期找出法院所在城市的最低温度
6. 通过律师事务所名称找出律师事务所地址
7. 通过律师事务所地址找出省份, 城市信息
8. 通过律师事务所的省份, 城市和1中的日期找出律师事务所所在城市的最低温度

可用API如下：
get_company_info
参数:公司名称or公司简称or公司代码
获取上市公司基本信息。基本信息有公司名称, 公司简称, 英文名称, 关联证券, 公司代码_股票代码, 曾用简称, 所属市场, 所属行业, 成立日期, 上市日期, 法人代表, 总经理 ,董秘, 邮政编码, 注册地址, 办公地址, 联系电话, 传真, 官方网址, 电子邮箱, 入选指数, 主营业务, 经营范围, 机构简介, 每股面值, 首发价, 首发募资净额, 首发主承销商

get_company_register
参数:公司名称
公司工商照面信息。工商照面信息有公司名称, 登记状态, 统一社会信用代码, 法定代表人, 注册资本, 成立日期, 企业地址, 联系电话, 联系邮箱, 注册号, 组织机构代码, 参保人数, 行业一级, 行业二级, 行业三级, 曾用名, 企业简介,经营范围

get_company_register_name
参数:统一社会信用代码
根据统一社会信用代码查询公司名称

get_sub_company_info
参数:子公司名称
根据被投资的子公司名称获得投资该公司的上市公司全称, 上市公司关系, 上市公司参股比例, 上市公司投资金额

get_sub_company_info_list
参数:上市公司（母公司）的名称
根据上市公司（母公司）的名称查询该公司投资的所有子公司信息列表, 上市公司关系, 参股比例, 投资金额，公司名称

get_legal_document
参数:案号
根据法律裁判文书的案号查询该法律裁判文书的相关信息:关联公司, 标题, 案号, 文书类型, 原告, 被告, 原告律师事务所, 被告律师事务所, 案由, 涉案金额, 判决结果, 日期, 文件名

get_legal_document_list
参数:关联公司名称
根据关联公司名称查询该公司涉及的所有案件即关联的法律裁判文书:关联公司, 标题, 案号, 文书类型, 原告, 被告, 原告律师事务所, 被告律师事务所, 案由, 涉案金额, 判决结果, 日期, 文件名

get_court_info
参数:法院名称
根据法院名称查询法院基础相关信息：法院名称, 法院负责人, 成立日期, 法院地址, 法院联系电话, 法院官网

get_court_code
参数:法院名称或者法院代字
根据法院名称或者法院代字查询法院代字等相关数据：法院名称, 行政级别, 法院级别, 法院代字, 区划代码, 级别

get_lawfirm_info
参数:律师事务所名称
根据律师事务所名称查询律师事务所信息：律师事务所名称, 律师事务所唯一编码, 律师事务所负责人, 事务所注册资本, 事务所成立日期, 律师事务所地址, 通讯电话, 通讯邮箱, 律所登记机关

get_lawfirm_log
参数:律师事务所名称
根据律师事务所名称查询律师事务所统计数据：律师事务所名称, 业务量排名, 服务已上市公司, 报告期间所服务上市公司违规事件, 报告期所服务上市公司接受立案调查

get_address_info
参数:地址
根据地址查该地址对应的省市区：省份, 城市, 区县

get_address_code
参数:省份,城市,区县三者组合
根据省市区查询地址编信息：城市区划代码, 区县区划代码

get_temp_info
参数:日期,省份,城市三者组合
根据日期及省份城市查询天气相关信息：天气, 最高温度, 最低温度, 湿度

get_legal_abstract
参数:案号
根据法律裁判文书的案号查询：文件名, 文本摘要

get_xzgxf_info
参数:案号
根据法律裁判文书的案号查询限制高消费相关信息:限制高消费企业名称, 案号, 法定代表人, 申请人, 涉案金额, 执行法院, 立案日期, 限高发布日期

get_xzgxf_info_list
参数:关联公司名称
根据企业名称查询所有限制高消费相关信息列表

注意：
字段‘法院代字’可以通过字段‘案号’获取,字段‘案号’通常由年份、法院代字和案件序号三部分组成，年份用()括起来，如：(2020)赣0781民初1260号中法院代字是赣0781案件序号是民初1260号、(2019)川01民终12104号中法院代字是川01案件序号是民终12104号。
通过案号解析出法院代字,再通过法院代字就能找到法院信息。

example：中山华利实业集团股份有限公司注册与办公的登记地址是否相同？该公司投资的子公司有多少家？投资总额为多少？
answer:
1. 通过公司名和get_company_info找出注册地址和办公地址
2. 通过公司名找出子公司信息列表的总数和上市公司投资金额

example：深圳希润融资租赁有限公司涉及案件中，该公司作为原告的涉案金额第二高的案件选择的律师事务所的成立时间是？
answer:
1. 通过公司名找出关联的案件列表
2. 找出满足原告包含深圳希润融资租赁有限公司并且涉案金额第二高的案件中的原告律师事务所
3. 通过律师事务所名称找出事务所成立日期

example：代码为300682的公司的子公司是否有涉诉？是否存在2019年在广东省广州市天河区员村一横路9号审理的财产损害案件？如果有，该涉诉子公司的注册资本是多少？被300682投资的金额为？
answer:
1. 通过公司代码找出公司名称
2. 通过公司名称找出子公司列表
3. 遍历子公司信息列表，使用每个子公司名称和get_legal_document_list找出所有涉诉案件。
4. 如果有涉诉，检查案件信息中是否存在2019年在广东省广州市天河区员村一横路9号审理的财产损害案件。
5. 如果存在上述案件，使用该涉诉子公司的名称和get_company_register获取注册资本。
6. 通过该子公司名称找出子公司信息中的上市公司投资金额

example：无锡东峰佳品科技发展有限公司对应的公司是否被限制高消费？如果是被限制高消费的最大涉案金额为（保留1位小数）？该案件对应的案号为？该案件的审理法院是？该法院的地址所在区县是？
answer:
1. 通过公司名找出限制高消费列表
2. 遍历限制高消费列表，找出其中涉案金额最大那条限制高消费，再找出其中的涉案金额和案号。
3. 通过案号解析出法院代字
4. 通过法院代字找出法院名称
5. 通过法院名称找出法院地址
6. 通过法院代字找出法院的区县

example：请问一下，300674的法定代表人及工商电话注册资本是多少亿元？请保留2位小数。
answer:
1. 分析出300674是公司代码,用公司代码找出公司名称
2. 通过公司名称找出法定代表人、联系电话和注册资本
3. 对数据保留2位小数

example：机构代码为91110113344302387N的公司涉诉文书中，主要位于哪一年？涉诉文书较多的那一年，和该公司对立方所请最多律师事务所的负责人是？
answer:
1. 通过机构代码找出公司名称
2. 通过公司名称找涉诉文书
3. 分析出涉诉文书列表，找出日期中年份出现频率最高的那一年
4. 分析年份出现最多的文书中对方请的律师事务所，找出出现频率最高的那个律师事务所
5. 通过律师事务所找出律师事务所负责人

请按给出以下问题的逻辑链。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
<原始问题>
{query}
</原始问题>
"""
