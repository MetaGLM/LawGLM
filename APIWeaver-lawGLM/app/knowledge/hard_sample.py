import json
import re


tmp = [{'key': '多地址查询题',
     'question': '(2019)川01民初4929号案件中，审理当天原告的律师事务所与被告的律师事务所所在地区的最高温度相差多少度？',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询(2019)川01民初4929号案件的审理当天，原告的律师事务所与被告的律师事务所所在地区的最高温度，并计算这两个地区的最高温度之差。
2. 分析解题路径：
   - 第一步：根据案号查询案件信息，获取原告律师事务所和被告律师事务所。
   - 第二步：根据律师事务所名称查询其所在地区信息。
   - 第三步：根据日期和地区查询天气信息，获取最高温度。
   - 第四步：计算原告律师事务所与被告律师事务所所在地区的最高温度差值。
3. 分析参数：
    - 输入参数：案号 (LegalDoc.案号)
    - 结果参数：原告律师事务所 (LegalDoc.原告律师事务所), 被告律师事务所 (LegalDoc.被告律师事务所), 日期 (LegalDoc.日期), 省份 (AddrInfo.省份), 城市 (AddrInfo.城市), 最高温度 (TempInfo.最高温度)
    - 中间参数：律师事务所名称 (LawfirmInfo.律师事务所名称), 地址 (LawfirmInfo.律师事务所地址)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document 接口，参数为 {'query_conds': {'案号': '(2019)川01民初4929号'}, 'need_fields': ['原告律师事务所', '被告律师事务所', '日期']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "获取律师事务所所在地区信息",
    "type": "查询",
    "suggestion": "对于步骤一得到的原告律师事务所和被告律师事务所，逐一调用 /get_lawfirm_info 接口，参数为 {'query_conds': {'律师事务所名称': '律师事务所名称'}, 'need_fields': ['律师事务所地址']}",
    "table_name": "LawfirmInfo",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "获取律师事务所所在地区的最高温度",
    "type": "查询",
    "suggestion": "对于步骤二得到律师事务所地址，逐一调用 /get_address_info 接口获取省份和城市，参数为 {'query_conds': {'地址': '原告律师事务所地址'}, 'need_fields': ['省份', '城市', '区县']}",
    "table_name": "AddrInfo, TempInfo",
    "is_necessary": "necessary",
    "base_on_step": [2]
  },
 {
    "step": 4,
    "goal": "获取律师事务所所在地区的最高温度",
    "type": "查询",
    "suggestion": "对于步骤三得到律师事务所所在省份和城市，逐一调用 /get_temp_info 接口获取日期和地区对应的最高温度",
    "table_name": "AddrInfo, TempInfo",
    "is_necessary": "necessary",
    "base_on_step": [3]
  },
  {
    "step": 5,
    "goal": "计算原告律师事务所与被告律师事务所所在地区的最高温度差值",
    "type": "计算",
    "suggestion": "用被告律师事务所所在地区的最高温度减去原告律师事务所所在地区的最高温度",
    "table_name": "TempInfo",
    "is_necessary": "necessary",
    "base_on_step": [4]
  }
]
```
'''}]



SAMPLE = [
    {'key': '涉案法院排序题（针对法院级别的题目如获取审理级别最高的法院）', 'question': '上海建工集团股份有限公司涉诉的案子中审理最高级别的法院名称是？\n `天能电池集团股份有限公司`涉诉的案子有多少起？其中最高级别的法院名称是？在北京审理的有几起？', 'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询上海建工集团股份有限公司涉诉的案件数量，并了解其中最高级别的法院名称。
2. 分析解题路径：
   - 第一步：根据公司名称查询其所有涉诉案件信息。
   - 第二步：对法院级别进行排序。
   - 第三步：找出最高级别的法院名称。
3. 分析参数：
    - 输入参数：公司名称 (CompanyRegister.公司名称)
    - 结果参数：案号 (LegalDoc.案号), 法院名称 (CourtInfo.法院名称), 法院级别 (CourtCode.法院级别)
    - 中间参数：案号 (LegalDoc.案号)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "根据公司名称查询其所有涉诉案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document_list 接口，参数为 {'query_conds': {'关联公司': '上海建工集团股份有限公司'}, 'need_fields': ['案号']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "对法院进行排序",
    "type": "查询",
    "suggestion": "使用 sort_court_level 对案号进行排序，输入是第一步结果",
    "table_name": "CourtCode",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "找出最高级别的法院名称",
    "type": "列举",
    "suggestion": "从第二步结果中找出最高级别的法院名称",
    "table_name": "CourtCode",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
# 如果还有过滤操作记得使用 `filter_legal_docs` 
'''},
    {'key': '案件筛选排序题',
     'question': '沈阳先锋工程机械销售有限公司涉及案件中，该公司作为原告的涉案金额第二高的案件由哪家法院审判？',
     'sample': '''
推理流程：
```md
1. 明确问题
    用户需要查询沈阳先锋工程机械销售有限公司涉及的案件中，该公司作为原告的涉案金额第二高的案件，并了解该案件由哪家法院审判。
2. 分析解题路径：
   - 第一步：根据公司名称查询所有相关案件信息。
   - 第二步：过滤出该公司作为原告的案件。
   - 第三步：根据涉案金额对案件进行排序，找出涉案金额第二高的案件。
   - 第四步：根据案号获取审理该案件的法院名称。
3. 分析参数：
    - 输入参数：公司名称 (LegalDoc.关联公司)
    - 结果参数：法院名称 (CourtInfo.法院名称)
    - 中间参数：案件列表 (LegalDoc), 涉案金额 (LegalDoc.涉案金额), 原告 (LegalDoc.原告)
```
执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取所有相关案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document_list 接口，参数为 {'query_conds': {'关联公司': '沈阳先锋工程机械销售有限公司'}, 'need_fields': ['案号', '原告', '涉案金额']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "过滤出该公司作为原告的案件",
    "type": "过滤",
    "suggestion": "使用 filter_legal_docs 函数，参数为 {'原告': '沈阳先锋工程机械销售有限公司'}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "根据涉案金额对案件进行排序,并找出涉案金额第二高的案件",
    "type": "计算",
    "suggestion": "调用 /rank 接口，参数为 {'data_list': 案件列表, 'key': '涉案金额', 'is_desc': True}" 然后取出涉案金额第二高的案件信息,
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [2]
  },
  {
    "step": 4,
    "goal": "获取该案件的律师事务所信息",
    "type": "查询",
    "suggestion": "使用 get_court_code_by_case_number 函数，参数为 {'query_conds': {'案号': '第三步的案号']}, 'need_fields': []}",
    "table_name": "CourtCode",
    "is_necessary": "necessary",
    "base_on_step": [3]
  }
]
```
'''},
    {'key': '案号参与者查找题（针对获胜方的查找）',
     'question': '(2020)苏01民终1783号获胜方的组织机构的编码是？',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询案号为`(2020)苏01民终1783号`的胜诉方的组织机构代码。
2. 分析解题路径：
   - 第一步：根据案号查询裁判文书相关信息，获取胜诉方（原告或被告）。
   - 第二步：根据胜诉方名称查询其工商信息，获取组织机构代码。
3. 分析参数：
   - 输入参数：案号 (LegalDoc.案号)
   - 结果参数：胜诉方名称 (LegalDoc.原告/被告), 组织机构代码 (CompanyRegister.统一社会信用代码),判决结果 (LegalDoc.判决结果)
   - 中间参数：胜诉方名称 (LegalDoc.原告/被告)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取案号为(2020)苏01民终1783号的裁判文书信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document 接口，参数为 {'query_conds': {'案号': '(2020)苏01民终1783号'}, 'need_fields': ['原告', '被告', '判决结果']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "确定胜诉方",
    "type": "计算",
    "suggestion": "根据步骤一获取的判决结果，判断胜诉方是原告还是被告",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "获取胜诉方的组织机构代码",
    "type": "查询",
    "suggestion": "调用 /get_company_register 接口，参数为 {'query_conds': {'公司名称': '胜诉方名称'}, 'need_fields': ['统一社会信用代码']}",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
'''},
    {'key': '案号信息筛选（针对案件本身信息，如年份，案由，金额，原告等）',
     'question': '原告是安徽安利材料科技股份有限公司涉案金额不为0的案件审理法院是哪家法院？ \n 查询一下光明乳业股份有限公司涉及的案件中，审理时间发生于2021年发生的执行案件有几次？',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询安徽安利材料科技股份有限公司作为原告且案金额不为0的案件审理法院是哪家法院。
2. 分析解题路径：
   - 第一步：根据公司名称查询其所有作为原告的涉诉案件信息。
   - 第二步：过滤第一步中的结果过滤条件为原告：安徽安利材料科技股份有限公司，最小涉案金额：0。
   - 第三步：根据案号查询法院名称。
3. 分析参数：
    - 输入参数：公司名称 (LegalDoc.关联公司), 原告 (LegalDoc.原告)
    - 结果参数：案号 (LegalDoc.案号), 审理法院 (CourtInfo.法院名称)
    - 中间参数：案件列表 (LegalDoc), 法院信息 (CourtInfo)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "根据公司名称查询其所有作为原告的涉诉案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document_list 接口，参数为 {'query_conds': {'关联公司': '安徽安利材料科技股份有限公司'}, 'need_fields': ['案号', '原告', '涉案金额']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "过滤第一步中的结果过滤条件为原告：安徽安利材料科技股份有限公司，最小涉案金额：0。",
    "type": "过滤",
    "suggestion": "使用 filter_legal_docs 函数过滤案件，参数为第一步的结果list 和 {'原告': '安徽安利材料科技股份有限公司','最小涉案金额':0}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "根据案号查询法院名称",
    "type": "查询",
    "suggestion": "使用 get_court_code_by_case_number 函数，参数为 {'query_conds': {'案号': '第二步中的案号'}, 'need_fields': []}",
    "table_name": "CourtInfo",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
'''},
    {'key': '案号筛选查询题（有条件案件的筛选并查询参与方）',
     'question': '阿拉尔新农乳业有限责任公司作为原告雇佣的律师事务所的联系方式是什么？\n 优地网络有限公司是否存在2019年在广东省广州市天河区员村一横路9号审理的财产损害案件？',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询阿拉尔新农乳业有限责任公司雇佣的律师事务所的联系方式。
2. 分析解题路径：
   - 第一步：根据公司名称查询其所有涉诉案件信息。
   - 第二步：过滤第一步中的结果，找出阿拉尔新农乳业有限责任公司作为原告或被告的案件，并获取对应的律师事务所信息。
   - 第三步：根据律师事务所名称查询律师事务所的联系方式。
3. 分析参数：
    - 输入参数：公司名称 (LegalDoc.关联公司), 原告 (LegalDoc.原告), 被告 (LegalDoc.被告), 原告律师事务所 (LegalDoc.原告律师事务所), 被告律师事务所 (LegalDoc.被告律师事务所)
    - 结果参数：律师事务所名称 (LawfirmInfo.律师事务所名称), 联系方式 (LawfirmInfo.通讯电话)
    - 中间参数：案件列表 (LegalDoc), 律师事务所信息 (LawfirmInfo)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "根据公司名称查询其所有涉诉案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document_list 接口，参数为 {'query_conds': {'关联公司': '阿拉尔新农乳业有限责任公司'}, 'need_fields': ['案号', '原告', '被告', '原告律师事务所', '被告律师事务所']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "过滤第一步中的结果，找出阿拉尔新农乳业有限责任公司作为原告或被告的案件，并获取对应的律师事务所信息",
    "type": "过滤",
    "suggestion": "使用 filter_legal_docs 函数过滤案件，参数为第一步的结果list 和 {'原告': '阿拉尔新农乳业有限责任公司'}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "根据律师事务所名称查询律师事务所的联系方式",
    "type": "查询",
    "suggestion": "调用 /get_lawfirm_info 接口，参数为 {'query_conds': {'律师事务所名称': '第二步中获取的律师事务所名称'}, 'need_fields': ['通讯电话', '通讯邮箱']}",
    "table_name": "LawfirmInfo",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
'''},
    {'key': '子公司查询排序题',
     'question': '天津七一二通信广播股份有限公司投资金额最高的子公司与投资最低的子公司注册地址分别是？',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询天津七一二通信广播股份有限公司投资金额最高的子公司与投资金额最低的子公司，并了解这两家子公司的注册地址。
1. 分析解题路径：
   - 第一步：根据公司名称查询其投资的所有子公司信息列表。
   - 第二步：根据投资金额对子公司列表进行排序，找出投资金额最高和最低的子公司。
   - 第三步：根据子公司名称查询其注册地址。
2. 分析参数：
    - 输入参数：公司名称 (SubCompanyInfo.关联上市公司全称)
    - 结果参数：子公司名称 (SubCompanyInfo.公司名称), 投资金额 (SubCompanyInfo.上市公司投资金额), 注册地址 (CompanyRegister.企业地址)
    - 中间参数：子公司列表 (SubCompanyInfo)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取子公司信息列表",
    "type": "查询",
    "suggestion": "调用 /get_sub_company_info_list 接口，参数为 {'query_conds': {'关联上市公司全称': '天津七一二通信广播股份有限公司'}, 'need_fields': ['公司名称', '上市公司投资金额']}",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "找出投资金额最高和最低的子公司并输出",
    "type": "计算",
    "suggestion": "使用 /rank 接口对步骤一得到的子公司列表进行排序，排序键为 '上市公司投资金额'，分别取排序后的第一个和最后一个元素，并打印",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "获取子公司的注册地址",
    "type": "查询",
    "suggestion": "对于步骤二得到的子公司名称，调用 /get_company_register 接口，参数为 {'query_conds': {'公司名称': '子公司名称'}, 'need_fields': ['企业地址']}",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
# 需要打印符合条件的子公司

'''},
    {'key': '子公司查询过滤（针对子公司信息，如投资金额持股比例）',
     'question': '金堆城钼业股份有限公司投资过亿的全资子公司分别是？这些子公司的统一社会信用代码是?',
     'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询金堆城钼业股份有限公司投资金额超过一亿元的全资子公司，并了解这些子公司的统一社会信用代码。
2. 分析解题路径：
   - 第一步：根据上市公司名称查询其所有子公司信息。
   - 第二步：使用过滤函数过滤出投资金额超过一亿元且参股比例为100%的子公司。
   - 第三步：获取这些子公司的统一社会信用代码及注册地址信息。
3. 分析参数：
    - 输入参数：公司全称 (CompanyInfo.公司名称)
    - 结果参数：子公司名称 (SubCompanyInfo.公司名称), 统一社会信用代码 (CompanyRegister.统一社会信用代码)
    - 中间参数：子公司名称 (SubCompanyInfo.公司名称)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取金堆城钼业股份有限公司的所有子公司信息",
    "type": "查询",
    "suggestion": "调用 /get_sub_company_info_list 接口，参数为 {'query_conds': {'关联上市公司全称': '金堆城钼业股份有限公司'}, 'need_fields': ['公司名称', '上市公司投资金额', '上市公司参股比例']}",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "筛选出投资金额超过一亿元且参股比例为100%的子公司，并打印",
    "type": "过滤",
    "suggestion": "使用 filter_sub_company 函数进行过滤，参数为第一步的结果以及 {'最小投资金额': '1亿', '最小持股比例': 100}",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "获取子公司的统一社会信用代码",
    "type": "查询",
    "suggestion": "对于步骤二得到的子公司列表，使用for循环调用 /get_company_register 接口，参数为 {'query_conds': {'公司名称': '子公司名称'}, 'need_fields': ['统一社会信用代码']}",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
# 需要打印符合条件的子公司
'''},
    {'key': '子公司信息筛选（针对子公司信息，如子公司地址法人编码等）',
     'question': '金堆城钼业股份有限公司有没有注册在陕西省西安市高新区高新技术开发区锦业一路88号A座二、三层的子公司',
     'sample': '''推理流程：
```md
1. 明确问题
   用户需要查询金堆城钼业股份有限公司是否有注册在陕西省西安市高新区高新技术开发区锦业一路88号A座二、三层的子公司。
2. 分析解题路径：
   - 第一步：根据上市公司名称查询其所有子公司信息。
   - 第二步：获取这些子公司的注册地址信息。
   - 第三步：判断子公司的注册地址是否为陕西省西安市高新区高新技术开发区锦业一路88号A座二、三层。
3. 分析参数：
    - 输入参数：公司全称 (CompanyInfo.公司名称), 地址 (AddrInfo.地址)
    - 结果参数：子公司名称 (SubCompanyInfo.公司名称), 注册地址 (CompanyRegister.企业地址)
    - 中间参数：子公司名称 (SubCompanyInfo.公司名称)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取金堆城钼业股份有限公司的所有子公司信息",
    "type": "查询",
    "suggestion": "调用 /get_sub_company_info_list 接口，参数为 {'query_conds': {'关联上市公司全称': '金堆城钼业股份有限公司'}, 'need_fields': ['公司名称']}",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "获取子公司的注册地址",
    "type": "查询",
    "suggestion": "对于步骤一得到的子公司列表，使用for循环调用 /get_company_register 接口，参数为 {'query_conds': {'公司名称': '子公司名称'}, 'need_fields': ['企业地址']}",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "判断子公司注册地址是否为目标地址",
    "type": "计算",
    "suggestion": "将步骤二得到的企业地址与目标地址进行比较，如果一致则说明存在注册在目标地址的子公司",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```
'''},
    {'key': '地址查询题（查询天气区划代码）',
         'question': '(2020)浙0108民初565号案件中，审理当天审理法院的天气情况是？',
         'sample': '''
推理流程：
```md
1. 明确问题
   用户需要查询(2020)浙0108民初565号案件审理当天的审理法院所在地区的天气情况。
2. 分析解题路径：
   - 第一步：根据案号查询案件信息，获取审理日期。
   - 第二步：根据案号获取审理法院的名称。
   - 第三步：根据法院名称查询其所在地区信息。
   - 第四步：根据日期和地区查询天气信息。
3. 分析参数：
    - 输入参数：案号 (LegalDoc.案号)
    - 结果参数：日期 (LegalDoc.日期), 省份 (AddrInfo.省份), 城市 (AddrInfo.城市), 天气情况 (TempInfo.天气)
    - 中间参数：法院名称 (CourtCode.法院名称), 地址 (CourtInfo.法院地址)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取案件信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document 接口，参数为 {'query_conds': {'案号': '(2020)浙0108民初565号'}, 'need_fields': ['日期']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "获取审理法院名称",
    "type": "查询",
    "suggestion": "调用 get_court_code_by_case_number 函数，参数为 {'query_conds': {'案号': '(2020)浙0108民初565号'}, 'need_fields': []}",
    "table_name": "CourtCode",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 3,
    "goal": "获取法院所在地区信息",
    "type": "查询",
    "suggestion": "调用 /get_court_info 接口，参数为 {'query_conds': {'法院名称': '审理法院名称'}, 'need_fields': ['法院地址']}",
    "table_name": "CourtInfo",
    "is_necessary": "necessary",
    "base_on_step": [2]
  },
  {
    "step": 4,
    "goal": "获取法院所在地区的天气情况",
    "type": "查询",
    "suggestion": "调用 /get_address_info 接口，参数为 {'query_conds': {'地址': '法院地址'}, 'need_fields': ['省份', '城市', '区县']}",
    "table_name": "AddrInfo",
    "is_necessary": "necessary",
    "base_on_step": [3]
  },
  {
    "step": 5,
    "goal": "获取天气情况",
    "type": "查询",
    "suggestion": "调用 /get_temp_info 接口，参数为 {'query_conds': {'省份': '省份', '城市': '城市', '日期': '日期'}, 'need_fields': ['天气', '最高温度', '最低温度', '湿度']}",
    "table_name": "TempInfo",
    "is_necessary": "necessary",
    "base_on_step": [1, 4]
  }
]
```
'''},
    {'key': '连续查询题(针对简单的连续查询)',
     'question': '金迪克的子公司的一级行业是什么\n(2020)津03民终1728号案件中的原告事务所服务过多少家上市公司\n查询一下光明乳业股份有限公司涉及的案件总额是多少，有多少家子公司？\n公司的全称为浙江海正药业股份有限公司，用户需要查询该公司的法人信息及电话。',
     'sample': ''''
推理流程：
```md
1. 明确问题
   用户需要查询金迪克的子公司所属的一级行业。
2. 分析解题路径：
   - 第一步：根据公司简称`金迪克`，查询其公司全称。
   - 第二步：根据公司全称获取该公司投资的所有子公司信息。
   - 第三步：根据子公司信息获取这些子公司的一级行业。
3. 分析参数：
   - 输入参数：公司简称 (CompanyInfo.公司简称)
   - 结果参数：子公司名称 (SubCompanyInfo.公司名称), 子公司所属的一级行业 (CompanyRegister.行业一级)
   - 中间参数：公司全称 (CompanyInfo.公司名称), 子公司名称 (SubCompanyInfo.公司名称)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "获取金迪克的公司全称",
    "type": "查询",
    "suggestion": "调用 /get_company_info 接口，参数为 {'query_conds': {'公司简称': '金迪克'}, 'need_fields': ['公司名称']}",
    "table_name": "CompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "获取金迪克（全称）的所有子公司信息",
    "type": "查询",
    "suggestion": "调用 /get_sub_company_info_list 接口，参数为 {'query_conds': {'关联上市公司全称': '金迪克全称'}, 'need_fields': ['公司名称']}",
    "table_name": "SubCompanyInfo",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "获取金迪克的子公司的一级行业",
    "type": "查询",
    "suggestion": "对于步骤二得到的子公司列表，使用for循环调用 /get_company_register 接口，参数为 {'query_conds': {'公司名称': '子公司名称'}, 'need_fields': ['行业一级']}",
    "table_name": "CompanyRegister",
    "is_necessary": "necessary",
    "base_on_step": [2]
  }
]
```    
'''},
]





SAMPLE2 = [

    {'key': '法院.*不规则案号',
     'question': '19年江苏省高级人民法院判，民申6268号，法院判决胜诉方是哪个公司？胜诉方律师事务所是？', 'sample': '''
推理流程：
```md
1. 分析解题路径：
   - 第一步：根据法院名称查询其法院代字。
   - 第二步：根据年份、法院代字和案件编号拼凑标准案号。
   - 第三步：根据标准案号查询裁判文书相关信息。
   - 第四步：从判决结果中找到胜诉方律师事务所。
2. 分析参数：
    - 输入参数：法院名称 (CourtInfo.法院名称), 年份 (案号), 案件编号 (案号), 胜诉方律师事务所名称 (LegalDoc.原告律师事务所/被告律师事务所)
    - 结果参数：法院代字 (CourtCode.法院代字), 标准案号 (案号)
    - 中间参数：法院信息 (CourtInfo), 法院代码信息 (CourtCode), 裁判文书信息 (LegalDoc)
```

执行步骤：
```json
[
  {
    "step": 1,
    "goal": "根据法院名称查询其法院代字",
    "type": "查询",
    "suggestion": "调用 /get_court_code 接口，参数为 {'query_conds': {'法院名称': '江苏省高级人民法院'}, 'need_fields': ['法院代字']}",
    "table_name": "CourtCode",
    "is_necessary": "necessary",
    "base_on_step": [0]
  },
  {
    "step": 2,
    "goal": "根据年份、法院代字和案件编号拼凑标准案号",
    "type": "计算",
    "suggestion": "将年份、法院代字和案件编号按照案号格式拼凑成标准案号，例如 '(2019)苏01民申6268号'",
    "table_name": "None",
    "is_necessary": "necessary",
    "base_on_step": [1]
  },
  {
    "step": 3,
    "goal": "根据标准案号查询裁判文书相关信息",
    "type": "查询",
    "suggestion": "调用 /get_legal_document 接口，参数为 {'query_conds': {'案号': '标准案号'}, 'need_fields': ['判决结果','原告律师事务所','被告律师事务所']}",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [2]
  },
  {
    "step": 4,
    "goal": "从判决结果中找到胜诉方律师事务所",
    "type": "计算",
    "suggestion": "判断判决结果中是否包含 '驳回'，如果不包含则胜诉律师事务所为原告律师事务所，否则为被告律师事务所",
    "table_name": "LegalDoc",
    "is_necessary": "necessary",
    "base_on_step": [3]
  }
]
```
    '''},

]

from Agent.llm import llm, super_eval


def get_sample(question):
    for i in SAMPLE2:
        if re.search(i['key'], question,re.DOTALL):
            return i['question'].split('\n')[0] + '\n' + i['sample']

    doc = ''
    for i, j in enumerate(SAMPLE):
        doc += f"题型id:{i + 1}\n题型说明:{j['key']}\n示例问题:{j['question']}\n---\n"
    prompt = f"""
{doc}
你的任务是找到以下问题的题型，请从以上{len(SAMPLE)}个文档中挑选最合适的1个，
你应该仔细对比题型说明而不是题目，有无过滤条件再题目中很好判断，无明确说明的即为无过滤
问题为：{question}
按照以下的json格式输出：
```json
{{"题型":"xxx","题型id":'int'}}
```
json输出正在 ```json ```内。
你的json:
"""
    str_id = super_eval(llm(prompt))['题型id']
    if isinstance(str_id, int) or (str_id.isdigit() and int(str_id) < len(SAMPLE)):
        return SAMPLE[int(str_id) - 1]['question'].split('\n')[0] + '\n' + SAMPLE[int(str_id) - 1]['sample']
    else:
        return SAMPLE[-1]['question'].split('\n')[0] + '\n' + SAMPLE[-1]['sample']


if __name__ == '__main__':
    print(get_sample('安利股份的子公司的一级行业是什么'))
