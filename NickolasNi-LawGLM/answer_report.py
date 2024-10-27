import json

import jsonlines
from tqdm import tqdm
from utils import read_jsonl
from config import *
import re


from match_tools.post_process import *


from match_tools.tools_register import get_tools, dispatch_tool
from match_tools.post_process import post_process_tool_results, prompt_final_result_without_API, prompt_4_API
from match_tools.pre_process import pre_process_company_tools, check_tool_and_args
from match_tools.schema import database_schema
from model import call_glm
from route import get_related_tables, route_tools, predict_direct_or_tools, enhance_tables
from utils import *
from match_tools.schema import get_schema_prompt, get_table_properties
from utils import parse_json_from_response
from prompts import system_sue_prompt, suggested_logic_chain_prompt
import time
import utils

system_prompt = """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。问题比较复杂需要通过逻辑链的方式逐步获取信息解决问题，即:分析问题用什么接口获取,该接口需要什么参数,该参数又要用什么接口获取，这样一步一步往上追溯。
问题包含整合报告和其他类型问题两类,要回答整合报告时query中会要求在整合报告中包含如下信息：公司的工商信息、子公司信息、裁判文书和限制高消费,有时候后面三项信息也会缺失。

问题处理流程如下：
1. 找出公司名称，query中直接包含或者通过工具查找
2. 调用get_integrated_report获取整合报告
3. 调用工具回答query中除了整合报告之外的其他类型问题，如果没有其他问题流程结束。此时千万要注意要排除掉整合报告中包含如下信息：公司的工商信息、子公司信息、裁判文书和限制高消费。

example:请问甘肃省敦煌种业集团股份有限公司的法人是谁，同时请写一份整合报告关于该公司的工商信息及子公司信息，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果）。
处理流程：
1. query已经包含了整合报告所用的公司名称：甘肃省敦煌种业集团股份有限公司
2. 调用get_integrated_report获取整合报告
3. 除了整合报告query中还问了公司的法人是谁，使用公司名称和get_company_info获取法人信息
此时整个流程已经结束，请不要忽略query中的'公司的工商信息及子公司信息'和'裁判文书及限制高消费'应为这些是整合报告所使用的信息。

example:龙建路桥股份有限公司关于工商信息（不包括公司简介）及投资金额过亿的全资子公司，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书（不需要判决结果）整合报告。
处理流程：
1. query已经包含了整合报告所用的公司名称：龙建路桥股份有限公司
2. 调用get_integrated_report获取整合报告
3. 除了整合报告所用到的信息，query中没有问其他问题，所以整个流程结束

example:请帮我写一份社会代码为913401007885810000的公司的整合报告，报告包含该公司公司关于工商信息（不包括公司简介）及投资金额过亿的全资子公司，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费。
处理流程：
1. 通过社会代码和工具get_company_register_name获取公司名称
2. 调用get_integrated_report获取该公司整合报告
3. 除了整合报告所用到的信息，query中没有问其他问题，所以整个流程结束

字段‘法院代字’可以通过字段‘案号’获取,字段‘案号’通常由年份、法院代字和案件序号三部分组成，年份用()括起来，如果问题中年份没有()请加上()变成标准的案号格式。如：(2020)赣0781民初1260号中法院代字是赣0781案件序号是民初1260号、(2019)川01民终12104号中法院代字是川01案件序号是民终12104号。
法院信息可以通过以下逻辑链获取：从‘案号’获取‘法院代字’，用‘法院代字’通过工具get_court_code获取‘法院名称’，用‘法院名称’通过工具get_court_info获取法院基础信息表（名录）CourtInfo。一般审理信息可以从法院信息获取，比如询问审理地址可以回答法院地址。
问题中涉及到的实体名称可能有噪音，法院名称一般格式是*省*市*区*法院。噪音包含但不限于：重复的叠字、法院名字中缺少'省市区'、律师事务所名称不完整。如"龙龙元建设集团股份有限公司"去噪变成"龙元建设集团股份有限公司"，如公司代码"330000116644"去噪变成"300164"，"信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司"去噪变成"信息产业电子第十一设计研究院科技工程股份有限公司"，如"北京丰台区人民法院"去噪变成"北京市丰台区人民法院"，"福建漳州中级人民法院"去噪变成"福建省漳州市中级人民法院"，"河南良承事务所"去噪变成"河南良承律师事务所"，"(2020)苏01民民终终1783号"去噪变成"(2020)苏01民终1783号"
天气信息的逻辑链需要日期,省份,城市三者组合。案件信息中包含了日期信息，也包含了律师事务所,公司信息,法院代字，省份,城市信息需要用详细地址和get_address_info工具获取，而详细地址一般是指公司地址、法院地址或律师事务所地址，分别需要通过公司名称和get_company_info获取公司地址、律所名称和get_lawfirm_info获取律所地址、法院名称和get_court_info获取法院地址，而法院名称可以通过法院代字和get_court_code获取。
当问'审理当天的天气'时需要通过案号和get_legal_document获取'日期',因为天气工具get_temp_info包含参数:'日期'.
当用户询问省份、城市、区县时必须通过地址信息和工具get_address_info获取,不能直接从详细地址、名称或者大模型内部信息中获取,必须通过给出的工具查询。当问天气和两地省市是否一致时都需要通过这样逻辑链进行查询。
当问法院的区县,城市或省份时，需要通过法院地址和get_address_info获取法院区县信息,如果没有法院地址需要先通过法院名称和get_court_info获取法院地址,如果没有法院名需要先通过'法院代字'和get_court_code获取法院名称。
当原本是公司名称的位置出现一串数字或者数字和字母组合，比如'原告是300077','91320722MA27RF9U87这家公司'、'91310114312234914L对应的公司'、'代码为300682的公司'，6位纯数字组成的是公司代码，18位数字和字母组成的是统一社会信用代码。此时的逻辑链是：如果是使用工具get_company_register_name和统一社会信用代码查找公司名称，再用工具get_company_info和公司名称查找公司信息，或者用工具get_company_info和公司代码查找公司信息。
查询子公司信息时可以通过母公司名和工具get_sub_company_info_list获取该公司的所有子公司信息。
当问题中要查询的信息在工具get_company_info和get_company_register都有时，必须先调用get_company_info。
当问到公司的两个属性分别在上市公司基本信息表和工商照面信息表时需要调用工具get_company_info和get_company_register查到所有属性,如问公司的统一社会代码和上市日期。
法人信息要通过公司名称和工具get_company_info获取字段'法人代表'
公司的注册地址可以通过公司名称和工具get_company_register获取字段'企业地址'
如果问题中涉及错别字等错误需要先修复。比如'玉门拓璞科技开发有限责任公司的地址在哪里？该公司被限告的涉案总额为？'其中的'被限告'应该改为'被限高'也就是限制高消费
当问一家公司的母公司信息时需要先根据该公司的名字和get_sub_company_info找到其母公司的名字后再通过其母公司名字找到母公司相关信息。
问题中有可能包含拼音,请把拼音转成中文再进行作答.如gongsi,zigongsi,anhao,fayuan,lvshishiwusuo,tianqi,xianzhigaoxiaofei分别代表了公司,子公司,案号,法院,律师事务所,天气和限制高消费

所提供的工具接口可以查询数据表的schema如下:
"""

system_prompt_get_report_first = """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。问题比较复杂需要通过逻辑链的方式逐步获取信息解决问题，即:分析问题用什么接口获取,该接口需要什么参数,该参数又要用什么接口获取，这样一步一步往上追溯。
问题包含整合报告和其他类型问题两类,如果整合报告和其他类型问题都包含时请先回答其他类型问题，最后再使用工具get_integrated_report回答整合报告。要回答整合报告时query中会要求在整合报告中包含如下信息：公司的工商信息、子公司信息、裁判文书和限制高消费,有时候后面三项信息也会缺失。在回答其他类型问题请不要回答整合报告中包含如下信息：公司的工商信息、子公司信息、裁判文书和限制高消费。这些整合报告所需信息一并由工具get_integrated_report内部获取。

比如query:"请问甘肃省敦煌种业集团股份有限公司的法人是谁，同时请写一份整合报告关于该公司的工商信息及子公司信息，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果）。"
分析：query中公司的工商信息、子公司信息、裁判文书和限制高消费都属于整合报告的内容所以要用工具get_integrated_report获得整合报告完整信息，而不能通过其他工具查询这些单个信息。
逻辑链：
1. 通过公司名称和工具get_company_info获取法人信息
2. 使用get_integrated_report获取整合报告.

字段‘法院代字’可以通过字段‘案号’获取,字段‘案号’通常由年份、法院代字和案件序号三部分组成，年份用()括起来，如果问题中年份没有()请加上()变成标准的案号格式。如：(2020)赣0781民初1260号中法院代字是赣0781案件序号是民初1260号、(2019)川01民终12104号中法院代字是川01案件序号是民终12104号。
法院信息可以通过以下逻辑链获取：从‘案号’获取‘法院代字’，用‘法院代字’通过工具get_court_code获取‘法院名称’，用‘法院名称’通过工具get_court_info获取法院基础信息表（名录）CourtInfo。一般审理信息可以从法院信息获取，比如询问审理地址可以回答法院地址。
问题中涉及到的实体名称可能有噪音，法院名称一般格式是*省*市*区*法院。噪音包含但不限于：重复的叠字、法院名字中缺少'省市区'、律师事务所名称不完整。如"龙龙元建设集团股份有限公司"去噪变成"龙元建设集团股份有限公司"，如公司代码"330000116644"去噪变成"300164"，"信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司"去噪变成"信息产业电子第十一设计研究院科技工程股份有限公司"，如"北京丰台区人民法院"去噪变成"北京市丰台区人民法院"，"福建漳州中级人民法院"去噪变成"福建省漳州市中级人民法院"，"河南良承事务所"去噪变成"河南良承律师事务所"，"(2020)苏01民民终终1783号"去噪变成"(2020)苏01民终1783号"
天气信息的逻辑链需要日期,省份,城市三者组合。案件信息中包含了日期信息，也包含了律师事务所,公司信息,法院代字，省份,城市信息需要用详细地址和get_address_info工具获取，而详细地址一般是指公司地址、法院地址或律师事务所地址，分别需要通过公司名称和get_company_info获取公司地址、律所名称和get_lawfirm_info获取律所地址、法院名称和get_court_info获取法院地址，而法院名称可以通过法院代字和get_court_code获取。
当问'审理当天的天气'时需要通过案号和get_legal_document获取'日期',因为天气工具get_temp_info包含参数:'日期'.
当用户询问省份、城市、区县时必须通过地址信息和工具get_address_info获取,不能直接从详细地址、名称或者大模型内部信息中获取,必须通过给出的工具查询。当问天气和两地省市是否一致时都需要通过这样逻辑链进行查询。
当问法院的区县,城市或省份时，需要通过法院地址和get_address_info获取法院区县信息,如果没有法院地址需要先通过法院名称和get_court_info获取法院地址,如果没有法院名需要先通过'法院代字'和get_court_code获取法院名称。
当原本是公司名称的位置出现一串数字或者数字和字母组合，比如'原告是300077','91320722MA27RF9U87这家公司'、'91310114312234914L对应的公司'、'代码为300682的公司'，6位纯数字组成的是公司代码，18位数字和字母组成的是统一社会信用代码。此时的逻辑链是：如果是使用工具get_company_register_name和统一社会信用代码查找公司名称，再用工具get_company_info和公司名称查找公司信息，或者用工具get_company_info和公司代码查找公司信息。
查询子公司信息时可以通过母公司名和工具get_sub_company_info_list获取该公司的所有子公司信息。
当问题中要查询的信息在工具get_company_info和get_company_register都有时，必须先调用get_company_info。
当问到公司的两个属性分别在上市公司基本信息表和工商照面信息表时需要调用工具get_company_info和get_company_register查到所有属性,如问公司的统一社会代码和上市日期。
法人信息要通过公司名称和工具get_company_info获取字段'法人代表'
公司的注册地址可以通过公司名称和工具get_company_register获取字段'企业地址'
如果问题中涉及错别字等错误需要先修复。比如'玉门拓璞科技开发有限责任公司的地址在哪里？该公司被限告的涉案总额为？'其中的'被限告'应该改为'被限高'也就是限制高消费
当问一家公司的母公司信息时需要先根据该公司的名字和get_sub_company_info找到其母公司的名字后再通过其母公司名字找到母公司相关信息。
问题中有可能包含拼音,请把拼音转成中文再进行作答.如gongsi,zigongsi,anhao,fayuan,lvshishiwusuo,tianqi,xianzhigaoxiaofei分别代表了公司,子公司,案号,法院,律师事务所,天气和限制高消费

所提供的工具接口可以查询数据表的schema如下:
"""

system_prompt_report = """你是一位语言学专家，尤其是金融法律领域，你的任务是根据用户给出的query，解析出关键信息。
关键信息包含以下4类：
1. 母公司，需要解析出母公司名称和排除字段.
2. 子公司. 需要解析出过滤条件和排除字段.
3. 裁判文书. 需要解析出所属公司、过滤条件和排除字段.
4. 限制高消费. 需要解析出所属公司、过滤条件和排除字段.

其中第2第3和第4类有可能没有在query中提到，此时对应关键信息的值填空字典{{}}.过滤条件和排除字段都都可能是多个，值是数组。
裁判文书和限制高消费都属于公司，'所属公司'是数组包含'母公司'和'子公司'中的一个或者两个，表示查询的是母公司、子公司或者母公司与子公司的该裁判文书或限制高消费。
过滤条件的元素是键值对，包含key：过滤的键值、operation：过滤操作，value：过滤的值。

对于不同的关键信息有不同的键值key选择
子公司可选择的过滤的键值key有如下：
{sub_company_keys}

裁判文书可选择的过滤的键值key有如下：
{legal_doc_keys}

限制高消费可选择的过滤的键值key有如下：
{xzgxf_keys}

过滤操作operation有如下：
<:小于某值
<=:小于等于某值
>:大于某值
>=:大于等于某值
!=:不等于某值
==: 等于某值
contain:包含某值
!contain:不包含某值
top:找出字段key的第几高/大，此时的value为int，比如value是1时表示找出key最高，value是2时表示找出key第二高，依次类推
bottom:找出字段key的倒数第几或者第几小，此时的value为int，比如value是1时表示找出key最小或者说倒数第一，value是2时表示找出key第二小或者倒数第二，依次类推
tops:找出字段key的前几高/大，此时的value为int，比如value是5时表示找出前5高的结果，依次类推
bottoms:找出字段key的前第几低/小，此时的value为int，比如value是5时表示找出前5小的结果，依次类推

以下是一些过滤例子：
投资金额过亿: "key":"上市公司投资金额","operation":">","value":"1亿"
投资金额不满百万: "key":"上市公司投资金额","operation":"<","value":"1百万"
全资子公司/圈资子公司: "key":"上市公司参股比例","operation":"contain","value":"100"
非全资子公司/不是全资子的公司/: "key":"上市公司参股比例","operation":"!contain","value":"100"
审理时间在2020年: "key":"日期","operation":"contain","value":"2020"
立案时间不在2021年: "key":"案号","operation":"!contain","value":"2021"
涉案金额不为0: "key":"涉案金额","operation":"!=","value":"0"
涉案金额大于10万: "key":"涉案金额","operation":">","value":"10万"

注意：
审理时间对应的字段是'日期'，对于'裁判文书'的立案时间对应的字段是'案号',而对于'限制高消费'的立案时间对应的字段是'立案日期'
当过滤时间时value应该是年份如2019，2020，2021，如果query中只说时间在19年或者20年等需要把value补全变成2019,2020,2021等。

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙建路桥股份有限公司关于工商信息（不包括公司简介和经营范围）及投资金额过亿的全资子公司，母公司及子公司的审理时间在2019年涉案金额不为0的裁判文书（不需要判决结果）整合报告。
```json
{{
    "母公司":{{"公司名称":"龙建路桥股份有限公司","排除字段":["公司简介","经营范围"]}},
    "子公司":{{"过滤条件":[{{"key":"上市公司投资金额","operation":">","value":"1亿"}},{{"key":"上市公司参股比例","operation":"contain","value":"100"}}],"排除字段":[]}},
    "裁判文书":{{"所属公司":["母公司","子公司"],"过滤条件":[{{"key":"日期","operation":"contain","value":"2019"}},{{"key":"涉案金额","operation":"!=","value":"0"}}],"排除字段":["判决结果"]}},
    "限制高消费":{{}}
}}
``` 

example：甘肃省敦煌种业集团股份有限公司关于工商信息及子公司信息，母公司及子公司的立案时间不在2020年涉案金额大于10万的裁判文书及限制高消费（不需要判决结果、限高发布日期）整合报告。
```json
{{
    "母公司":{{"公司名称":"甘肃省敦煌种业集团股份有限公司","排除字段":[]}},
    "子公司":{{"过滤条件":[],"排除字段":[]}},
    "裁判文书":{{"所属公司":["母公司","子公司"],"过滤条件":[{{"key":"案号","operation":"!contain","value":"2020"}},{{"key":"涉案金额","operation":">","value":"10万"}}],"排除字段":["判决结果"]}},
    "限制高消费":{{"所属公司":["母公司","子公司"],"过滤条件":[{{"key":"案号","operation":"!contain","value":"2020"}},{{"key":"涉案金额","operation":">","value":"10万"}}],"排除字段":["限高发布日期"]}}
}}
``` 
"""


def filter_sub_companies(sub_companies, investment_threshold):
    filtered_sub_companies = []
    sub_company_names = []
    for sub_company in sub_companies:
        try:
            investment = sub_company["上市公司投资金额"]
            investment = investment.replace("千", "*1e3")
            investment = investment.replace("万", "*1e4")
            investment = investment.replace("亿", "*1e8")
            investment = eval(investment)
        except Exception as e:
            investment = 0
        if sub_company.get("上市公司参股比例", "").__contains__("100") and investment > investment_threshold:
            sub_company_names.append(sub_company.get("公司名称", ""))
            filtered_sub_companies.append(sub_company)
    return filtered_sub_companies, sub_company_names


def filter_legal_docs(legal_docs, time_threshold, money_threshold):
    filtered_legal_docs = []
    for legal_doc in legal_docs:
        try:
            money = legal_doc["涉案金额"]
            money = money.replace("千", "*1e3")
            money = money.replace("万", "*1e4")
            money = money.replace("亿", "*1e8")
            money = eval(money)
        except Exception as e:
            money = 0
        if legal_doc.get("日期", "").__contains__(time_threshold) and money > money_threshold:
            del legal_doc["判决结果"]
            filtered_legal_docs.append(legal_doc)
    return filtered_legal_docs


def filter_legal_docs_lian(legal_docs, time_threshold, money_threshold):
    filtered_legal_docs = []
    for legal_doc in legal_docs:
        try:
            money = legal_doc["涉案金额"]
            money = money.replace("千", "*1e3")
            money = money.replace("万", "*1e4")
            money = money.replace("亿", "*1e8")
            money = eval(money)
        except Exception as e:
            money = ""
        if legal_doc.get("案号", "").__contains__(time_threshold) and money != money_threshold:
            del legal_doc["判决结果"]
            filtered_legal_docs.append(legal_doc)
    return filtered_legal_docs


def filter_xzgxf(all_xzgxf_docs, time_threshold, money_threshold):
    filtered_xzgxf_docs = []
    for xzgxf_doc in all_xzgxf_docs:
        try:
            money = xzgxf_doc["涉案金额"]
            money = money.replace("千", "*1e3")
            money = money.replace("万", "*1e4")
            money = money.replace("亿", "*1e8")
            money = eval(money)
        except Exception as e:
            money = ""
        if xzgxf_doc.get("立案日期", "").__contains__(time_threshold) and money != money_threshold:
            # del xzgxf_doc['判决结果']
            filtered_xzgxf_docs.append(xzgxf_doc)
    return filtered_xzgxf_docs


def filter_list(obj_list, filter_conditions):
    filtered_results = []
    for obj in obj_list:
        exclude = False
        try:
            for filter_condition in filter_conditions:
                key = filter_condition["key"]
                if key in obj.keys():
                    tool_result_value = obj[key]
                    operation = filter_condition["operation"]
                    value = filter_condition["value"]
                    if operation == "contain":
                        if not tool_result_value.__contains__(value):
                            exclude = True
                            break
                    elif operation == "!contain":
                        if tool_result_value.__contains__(value):
                            exclude = True
                            break
                    elif operation == "==":
                        if tool_result_value != value:
                            exclude = True
                            break
                    elif operation == "!=":
                        if tool_result_value == value:
                            exclude = True
                            break
                    elif operation in ["<", "<=", ">=", ">"]:
                        if tool_result_value == "":
                            exclude = True
                            break
                        tool_result_value_float = tool_result_value.replace("千", "*1e3")
                        tool_result_value_float = tool_result_value_float.replace("百", "*1e2")
                        tool_result_value_float = tool_result_value_float.replace("万", "*1e4")
                        tool_result_value_float = tool_result_value_float.replace("亿", "*1e8")
                        tool_result_value_float = eval(tool_result_value_float)

                        value_float = value.replace("千", "*1e3")
                        value_float = value_float.replace("百", "*1e2")
                        value_float = value_float.replace("万", "*1e4")
                        value_float = value_float.replace("亿", "*1e8")
                        value_float = eval(value_float)

                        if operation == "<":
                            if tool_result_value_float >= value_float:
                                exclude = True
                                break
                        elif operation == "<=":
                            if tool_result_value_float > value_float:
                                exclude = True
                                break
                        elif operation == ">":
                            if tool_result_value_float <= value_float:
                                exclude = True
                                break
                        elif operation == ">=":
                            if tool_result_value_float < value_float:
                                exclude = True
                                break
        except Exception as e:
            print_log(e)
        if not exclude:
            filtered_results.append(obj)
    return filtered_results


def get_suggested_logic_chain(query):
    try:
        prompt = suggested_logic_chain_prompt.format(query=query)
        messages = [{"role": "user", "content": prompt}]
        response = call_glm(messages, model="glm-4-0520")
        content = response.choices[0].message.content
        return content
    except Exception as e:
        print_log(e)
        return None


def run_report(query, provided_information):
    result = ""
    tokens_count = 0

    sub_company_keys = get_table_properties("sub_company_info")
    legal_doc_keys = get_table_properties("legal_doc")
    xzgxf_keys = get_table_properties("XzgxfInfo")
    sys_prompt = system_prompt_report.format(
        sub_company_keys=sub_company_keys, legal_doc_keys=legal_doc_keys, xzgxf_keys=xzgxf_keys
    )

    if provided_information:
        user_prompt = query + "\n已知信息：" + provided_information
    else:
        user_prompt = query
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
    for _ in range(3):
        try:
            response = call_glm(messages, model="glm-4-0520", temperature=0.11, top_p=0.11)
            message, response = parse_content_2_function_call(response.choices[0].message.content, response)
            tokens_count += response.usage.total_tokens
            # messages.append(response.choices[0].message.model_dump())
            messages.append(message)
            break
        except Exception as e:
            print_log(e)
    try:
        parsed_args = parse_json_from_response(message.get("content", ""))

        company_name = parsed_args.get("母公司").get("公司名称")
        company_excluded_num = len(parsed_args.get("母公司").get("排除字段"))
        params_company_register = {"query_conds": {"公司名称": company_name}, "need_fields": []}
        api_result_company_register = http_api_call_original("get_company_register", params_company_register)
        result = "Word_{}_companyregister1_{}_".format(
            company_name, str(len(api_result_company_register) - company_excluded_num)
        )

        if len(parsed_args.get("子公司")):
            params_sub_company_info_list = {
                "query_conds": {
                    "关联上市公司全称": company_name,
                },
                "need_fields": [],
            }
            api_result_sub_company_info_list = http_api_call_original(
                "get_sub_company_info_list", params_sub_company_info_list
            )
            if type(api_result_sub_company_info_list) == dict:
                api_result_sub_company_info_list = [api_result_sub_company_info_list]
            sub_company_excluded_num = len(parsed_args.get("子公司").get("排除字段"))
            sub_company_filter_conditions = parsed_args.get("子公司").get("过滤条件")
            api_result_sub_company_info_list = filter_list(
                api_result_sub_company_info_list, sub_company_filter_conditions
            )
            sub_company_names = [obj["公司名称"] for obj in api_result_sub_company_info_list]

            subcompany_arg_1 = len(api_result_sub_company_info_list)
            if subcompany_arg_1 == 0:
                subcompany_arg_2 = 0
            else:
                subcompany_arg_2 = len(api_result_sub_company_info_list[0]) - sub_company_excluded_num
            result = result + "subcompanyinfo{}_{}_".format(str(subcompany_arg_1), str(subcompany_arg_2))
        else:
            result = result + "subcompanyinfo0_0_"

        if len(parsed_args.get("裁判文书")):
            companies = parsed_args.get("裁判文书").get("所属公司")
            company_names_4_legal_docs = []
            if "母公司" in companies:
                company_names_4_legal_docs = [company_name]
            if "子公司" in companies and len(parsed_args.get("子公司")):
                company_names_4_legal_docs.extend(sub_company_names)

            all_legal_docs = []
            for company_name_4_legal_docs in company_names_4_legal_docs:
                params_legal_document_list = {
                    "query_conds": {"关联公司": company_name_4_legal_docs},
                    "need_fields": [],
                }
                api_result_legal_document_list = http_api_call_original(
                    "get_legal_document_list", params_legal_document_list
                )
                if type(api_result_legal_document_list) == list:
                    all_legal_docs.extend(api_result_legal_document_list)
                elif type(api_result_legal_document_list) == dict:
                    all_legal_docs.extend([api_result_legal_document_list])

            legal_docs_excluded_num = len(parsed_args.get("裁判文书").get("排除字段"))
            legal_docs_filter_conditions = parsed_args.get("裁判文书").get("过滤条件")
            api_result_legal_docs_list = filter_list(all_legal_docs, legal_docs_filter_conditions)

            legal_docs_arg_1 = len(api_result_legal_docs_list)
            if legal_docs_arg_1 == 0:
                legal_docs_arg_2 = 0
            else:
                legal_docs_arg_2 = len(api_result_legal_docs_list[0]) - legal_docs_excluded_num
            result = result + "legallist{}_{}_".format(str(legal_docs_arg_1), str(legal_docs_arg_2))
        else:
            result = result + "legallist0_0_"

        if len(parsed_args.get("限制高消费")):
            companies = parsed_args.get("限制高消费").get("所属公司")
            company_names_4_xzgxf_docs = []
            if "母公司" in companies:
                company_names_4_xzgxf_docs = [company_name]
            if "子公司" in companies and len(parsed_args.get("子公司")):
                company_names_4_xzgxf_docs.extend(sub_company_names)

            all_xzgxf_docs = []
            for company_name_4_xzgxf_docs in company_names_4_xzgxf_docs:
                params_xzgxf_docs = {
                    "query_conds": {"限制高消费企业名称": company_name_4_xzgxf_docs},
                    "need_fields": [],
                }
                api_result_xzgxf_docs = http_api_call_original("get_xzgxf_info_list", params_xzgxf_docs)
                if type(api_result_xzgxf_docs) == list:
                    all_xzgxf_docs.extend(api_result_xzgxf_docs)
                elif type(api_result_xzgxf_docs) == dict:
                    all_xzgxf_docs.extend([api_result_xzgxf_docs])

            xzgxf_docs_excluded_num = len(parsed_args.get("限制高消费").get("排除字段"))
            xzgxf_docs_filter_conditions = parsed_args.get("限制高消费").get("过滤条件")
            api_result_xzgxf_docs_list = filter_list(all_xzgxf_docs, xzgxf_docs_filter_conditions)

            xzgxf_docs_arg_1 = len(api_result_xzgxf_docs_list)
            if xzgxf_docs_arg_1 == 0:
                xzgxf_docs_arg_2 = 0
            else:
                xzgxf_docs_arg_2 = len(api_result_xzgxf_docs_list[0]) - xzgxf_docs_excluded_num
            result = result + "xzgxflist{}_{}".format(str(xzgxf_docs_arg_1), str(xzgxf_docs_arg_2))
        else:
            result = result + "xzgxflist0_0"
    except Exception as e:
        print_log(e)
    return result


def get_report(query, logic_chain):
    information = ""
    for per_logic in logic_chain:
        if type(per_logic) == list and len(per_logic) == 3:
            if len(str(per_logic[2])) <= 50:
                information = (
                    information
                    + "根据:"
                    + str(per_logic[0])
                    + "和接口:"
                    + str(per_logic[1])
                    + ",查询到:"
                    + str(per_logic[2])
                    + "\n"
                )
            elif not information.__contains__(str(per_logic[0])):
                information = information + str(per_logic[0]) + "\n"
        elif len(str(per_logic)) <= 38:
            information = information + str(per_logic) + "\n"
    report = run_report(query, information)
    return report


def run(query, tools, related_tables, update_message=True, suggested_logic_chain=False):
    retry_index = 0
    # report = get_report(query, [])

    while retry_index < 1:
        print_log(f"------------##retry_index:{retry_index}##------------")
        retry_index = retry_index + 1
        tokens_count = 0

        if suggested_logic_chain:
            logic_chain_str = get_suggested_logic_chain(query)
            user_query = query + "\n可以参考以下逻辑链：\n" + logic_chain_str
        else:
            user_query = query

        # if report:
        #     user_query = user_query + '\n已经获知整合报告为：' + report
        sys_prompt = system_prompt + get_schema_prompt(related_tables)
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_query}]

        logic_chain = []
        must_contained_info = set()
        for i in range(10):
            print_log(f"##第{i}轮对话##")
            pprint_log(messages)
            print_log("#" * 10)
            print_log("\n")

            for _ in range(3):
                try:
                    # response = call_glm(messages, model="glm-4-0520", tools=tools)
                    # response = call_glm(messages, model="glm-4-0520", tools=tools, do_sample=False)
                    response = call_glm(messages, model="glm-4-0520", tools=tools, temperature=0.11, top_p=0.11)
                    message, response = parse_content_2_function_call(response.choices[0].message.content, response)
                    tokens_count += response.usage.total_tokens
                    # messages.append(response.choices[0].message.model_dump())
                    messages.append(message)
                    break
                except Exception as e:
                    print_log(e)

            try:
                if response.choices[0].finish_reason == "tool_calls":
                    # tools_call = response.choices[0].message.tool_calls[0]
                    # tool_name = tools_call.function.name
                    # args = tools_call.function.arguments

                    tool_name = message["tool_calls"][0]["function"]["name"]
                    args = message["tool_calls"][0]["function"]["arguments"]
                    args = utils.check_company_name(tool_name, args, logic_chain, must_contained_info)
                    args, tool_name = check_area_4_temperature(tool_name, args, logic_chain, message)
                    if isinstance(args, dict):
                        args = json.dumps(args, ensure_ascii=False)
                    tool_id = message["tool_calls"][0]["id"]

                    tool_name, args = check_tool_and_args(tool_name, args, message, logic_chain, query)

                    if tool_name == "get_integrated_report":
                        report = get_report(query, logic_chain)
                        refined_answer = "整合报告为：" + report
                        logic_chain.append(["", "get_integrated_report", report])
                    else:
                        obs = dispatch_tool(tool_name, args, "007")
                        if obs.get("call_api_successfully", False):
                            obs, need_tools_4_data_process = post_process_tool_results(
                                obs, tool_name, args, logic_chain, query
                            )

                            if obs.get("refined_answer", ""):
                                if tool_name == "get_legal_document_list":
                                    obs["refined_answer"] = obs.get("refined_answer").split("法律文书信息如下")[0]
                                    obs["search_result"] = obs["refined_answer"]
                                elif tool_name == "get_sub_company_info_list":
                                    obs["refined_answer"] = obs.get("refined_answer").split("子公司信息如下")[0]
                                    obs["search_result"] = obs["refined_answer"]
                                elif tool_name == "get_xzgxf_info_list":
                                    if obs.get("refined_answer").__contains__("满足问题要求的限制高消费的信息如"):
                                        obs["refined_answer"] = obs.get("refined_answer").split(
                                            "满足问题要求的限制高消费的信息如"
                                        )[0]
                                        obs["search_result"] = obs["refined_answer"]

                            if obs.get("condition", ""):
                                if type(obs.get("condition", "")) == list:
                                    for condition in obs.get("condition", ""):
                                        must_contained_info.add(condition)
                                else:
                                    must_contained_info.add(obs.get("condition", ""))
                            # if need_tools_4_data_process:
                            #     tools.extend([all_tools.get('get_sum')])

                            if isinstance(obs, dict):
                                if "refined_answer" in obs.keys():
                                    refined_answer = obs.get("refined_answer", "")
                                else:
                                    refined_answer = json.dumps(obs, ensure_ascii=False)
                            else:
                                refined_answer = str(obs)

                            if (
                                isinstance(obs, dict)
                                and "condition" in obs.keys()
                                and "api" in obs.keys()
                                and "search_result" in obs.keys()
                                and obs.get("search_result", "")
                            ):
                                logic_chain.append(
                                    [obs.get("condition", ""), obs.get("api", ""), obs.get("search_result", "")]
                                )
                                if update_message:
                                    update_logic_chain_and_messages(obs.get("condition", ""), logic_chain, messages)
                            # else:
                            #     logic_chain.append(refined_answer)

                        else:
                            refined_answer = obs.get("refined_answer", "")
                    messages.append(
                        {
                            "role": "tool",
                            "content": f"{refined_answer}",
                            "tool_id": tool_id,
                            # "tool_id": tools_call.id
                        }
                    )
                else:
                    # if message['role'] == 'assistant' and (message['content'].__contains__('未提供') or message['content'].__contains__('未能')):
                    #     must_contained_info, tokens_count, messages, response = run(query, tools, related_tables, update_message=False)
                    # else:
                    print_log("###对话结束###")
                    # logic_chain.append(message['content'])
                    # information = '\n'.join(logic_chain)
                    information = ""
                    for per_logic in logic_chain:
                        if type(per_logic) == list and len(per_logic) == 3:
                            if str(per_logic[1]) == "get_integrated_report":
                                information = information + "整合报告为：" + str(per_logic[2]) + "\n"
                            else:
                                information = (
                                    information
                                    + "根据:"
                                    + str(per_logic[0])
                                    + "和接口:"
                                    + str(per_logic[1])
                                    + ",查询到:"
                                    + str(per_logic[2])
                                    + "\n"
                                )
                        else:
                            information = information + str(per_logic) + "\n"
                    information = information.strip()
                    if information.strip():
                        information = "<逻辑链>\n" + information + "\n</逻辑链>\n"

                    if (
                        query.__contains__("api")
                        or query.__contains__("API")
                        or query.__contains__("接口")
                        or query.__contains__("ＡＰＩ")
                    ):
                        final_prompt = prompt_final_result_without_API_report.format(
                            query=query, information=information, prompt_4_API=prompt_4_API
                        )
                    else:
                        final_prompt = prompt_final_result_without_API_report.format(
                            query=query, information=information, prompt_4_API=""
                        )
                    final_message = [{"role": "user", "content": final_prompt}]
                    response = call_glm(final_message, model="glm-4-0520")
                    # check_API(query, response, information)
                    retry_index = 10
                    break
            except Exception as e:
                print_log(e)
                time.sleep(4)
                break

    if retry_index == 10:
        return must_contained_info, tokens_count, messages, response, response.choices[0].message.content
    else:
        # final_message = [
        #     {"role": "system", "content": "你是一个法律专家，请根据你的专业知识回答用户的问题"},
        #     {"role": "user", "content": query}
        # ]
        # response = call_glm(final_message)
        # return [], tokens_count, [{"content": response.choices[0].message.content, "role": "assistant"}], response

        return must_contained_info, tokens_count, [{"content": query, "role": "assistant"}], query, query + "抱歉"
