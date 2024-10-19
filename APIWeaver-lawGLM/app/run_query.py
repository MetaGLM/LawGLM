from Agent.llm import llm_eval, llm
from api import call_api
import re
from Agent.Executor import Executor
from knowledge.tools import get_court_code_by_case_number

TABLES = [
    {
        "表名": "CompanyInfo",
        "属性值": [
            "公司名称",
            "公司简称",
            "英文名称",
            "关联证券",
            "公司代码",
            "曾用简称",
            "所属市场",
            "所属行业",
            "成立日期",
            "上市日期",
            "法人代表",
            "总经理",
            "董秘",
            "邮政编码",
            "注册地址",
            "办公地址",
            "联系电话",
            "传真",
            "官方网址",
            "电子邮箱",
            "入选指数",
            "主营业务",
            "经营范围",
            "机构简介",
            "每股面值",
            "首发价格",
            "首发募资净额",
            "首发主承销商",
        ],
        "key": ["公司名称"],
        "作用": "根据公司名称查询公司上市信息",
    },
    {
        "表名": "CompanyRegister",
        "属性值": [
            "公司名称",
            "登记状态",
            "统一社会信用代码",
            "法定代表人",
            "注册资本",
            "成立日期",
            "企业地址",
            "联系电话",
            "联系邮箱",
            "注册号",
            "组织机构代码",
            "参保人数",
            "行业一级",
            "行业二级",
            "行业三级",
            "曾用名",
            "企业简介",
            "经营范围",
        ],
        "key": ["公司名称"],
        "作用": "根据公司名称查询公司注册信息",
    },
    {
        "表名": "LegalDocument",
        "属性值": [
            "关联公司",
            "标题",
            "案号",
            "文书类型",
            "原告",
            "被告",
            "原告律师事务所",
            "被告律师事务所",
            "案由",
            "涉案金额",
            "判决结果",
            "日期",
            "文件名",
            "审理法院",
        ],
        "key": ["案号"],
        "作用": "通过案号查询裁判文书信息",
    },
    {
        "表名": "LegalAbstract",
        "属性值": ["文件名", "案号", "文本摘要"],
        "key": ["案号"],
        "作用": "通过案号查询文本摘要，如果用户要求总结，或者是获取按照摘要，请查询此表不要查询判决结果",
    },
    {
        "表名": "CourtInfo",
        "属性值": ["法院名称", "法院负责人", "成立日期", "法院地址", "法院联系电话", "法院官网"],
        "key": ["法院名称"],
        "作用": "通过法院名称查询法院信息",
    },
    {
        "表名": "CourtCode",
        "属性值": ["法院名称", "行政级别", "法院级别", "法院代字", "级别"],
        "key": ["法院名称"],
        "作用": "通过法院名称查询法院行政级别信息",
    },
    {
        "表名": "LawfirmInfo",
        "属性值": [
            "律师事务所名称",
            "律师事务所唯一编码",
            "律师事务所负责人",
            "事务所注册资本",
            "事务所成立日期",
            "律师事务所地址",
            "通讯电话",
            "通讯邮箱",
            "律所登记机关",
        ],
        "key": ["律师事务所名称"],
        "作用": "通过律师事务所名称，查询律师事务所基础信息",
    },
    {
        "表名": "LawfirmLog",
        "属性值": [
            "律师事务所名称",
            "业务量排名",
            "服务已上市公司",
            "报告期间所服务上市公司违规事件",
            "报告期所服务上市公司接受立案调查",
        ],
        "key": ["律师事务所名称"],
        "作用": "通过律师事务所名称，查询律师事务所业务信息",
    },
    {
        "表名": "AddressInfo",
        "属性值": ["地址", "省份", "城市", "区县"],
        "key": ["地址"],
        "作用": "通过地址查询省市区，查询后的结果可以用于查询天气和区划代码",
    },
    {
        "表名": "AddressCode",
        "属性值": ["省份", "城市", "城市区划代码", "区县", "区县区划代码"],
        "key": [{"省份", "城市", "区县"}],
        "作用": "通过省份，城市，区县三个字段查询区划代码，注意三个字段都是必填",
    },
    {
        "表名": "TempInfo",
        "属性值": ["日期", "省份", "城市", "天气", "最高温度", "最低温度", "湿度"],
        "key": [{"日期", "省份", "城市"}],
        "作用": "通过日期省份城市查询天气",
    },
    {
        "表名": "XzgxfInfo",
        "属性值": [
            "限制高消费企业名称",
            "案号",
            "法定代表人",
            "申请人",
            "涉案金额",
            "执行法院",
            "立案日期",
            "限高发布日期",
        ],
        "key": ["案号"],
        "作用": "通过限制高消费案号查询限制高消费信息",
    },
]


def question_entity_processing(question, ner):
    li = []
    query_res = []
    for i in ner["实体"]:
        li.append(i)
        if i["格式匹配为"] == "公司简称":
            param = {"query_conds": {"公司简称": i["名称"]}, "need_fields": ["公司名称"]}
            entity = call_api("/get_company_info", param, print_str=False)
            if entity:
                li.append(f"使用 {param} 查询结果:{entity}")
            query_res.append(entity)

        if i["格式匹配为"] == "公司代码":
            param = {"query_conds": {"公司代码": i["名称"]}, "need_fields": ["公司名称"]}
            entity = call_api("/get_company_info", param, print_str=False)
            if entity:
                li.append(f"使用 {param} 查询结果:{entity}")
            query_res.append(entity)

        elif i["格式匹配为"] == "统一社会信用代码":
            param = {"query_conds": {"统一社会信用代码": i["名称"]}, "need_fields": []}
            entity = call_api("/get_company_register_name", param, print_str=False)
            if entity:
                li.append(f"使用 {param} 查询结果:{entity}")
            query_res.append(entity)
        elif i["格式匹配为"] == "地址":
            param = {"query_conds": {"地址": i["名称"]}, "need_fields": []}
            entity = call_api("/get_address_info", param, print_str=False)
            if entity:
                li.append(f"使用 {param} 查询结果:{entity}")
                query_res.append(entity)
        elif i["格式匹配为"] == "法院名称":
            param = {"query_conds": {"法院名称": i["名称"]}, "need_fields": ["法院代字"]}
            entity = call_api("/get_court_code", param, print_str=False)
            if entity:
                li.append(f"使用 {param} 查询结果:{entity}")
                query_res.append(entity)

        if i["格式匹配为"] in ["公司名称", "统一社会信用代码"]:
            if re.search(re.escape(i["名称"]) + ".{0,6}(母公司|被投资|被控股)", question):
                if i["格式匹配为"] == "公司名称":
                    param = {"query_conds": {"公司名称": i["名称"]}, "need_fields": []}
                    entity = call_api("/get_sub_company_info", param, print_str=False)
                    if entity:
                        query_res.append(entity)
                        li.append(f"使用 {param} 查询母公司结果:{entity}")
                else:
                    param = {"query_conds": {"统一社会信用代码": i["名称"]}, "need_fields": []}
                    entity = call_api("/get_company_register_name", param, print_str=False)
                    param = {"query_conds": {"公司名称": entity["公司名称"]}, "need_fields": []}
                    entity = call_api("/get_sub_company_info", param, print_str=False)
                    if entity:
                        query_res.append(entity)
                        li.append(f"使用 {param} 查询母公司结果:{entity}")
    for i in query_res:
        if isinstance(i, dict):
            for k, v in i.items():
                li.append({"实体": v, "格式匹配为": k})
    return li


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    result = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return result


def format_history(history):
    s = ""
    for i in history:
        if isinstance(i, dict):
            s += str(i)
            s += "\n"
        else:
            break
    for i in history:
        if isinstance(i, str):
            s += "\n"
            s += i
    return s


def do_task(task_dic, depth=0):
    if depth > 3:
        return []
    dic = {
        "原告律师事务所": "律师事务所名称",
        "被告律师事务所": "律师事务所名称",
        # '被告律师事务所': '律师事务所名称',
    }
    pos_val = []
    for i in TABLES:
        if i["表名"] == task_dic["表名"]:
            pos_val = i["属性值"]
    need_fields = [i for i in task_dic["需要字段"] if i in pos_val]
    if len(need_fields) == 1 and need_fields[0] == "公司名称":
        return []
    url = f'/get_{camel_to_snake(task_dic["表名"])}'
    param = {"query_conds": task_dic["实体"], "need_fields": need_fields}

    res_dic = {}
    if url == "/get_legal_document" and "审理法院" in param["need_fields"]:
        param["need_fields"].remove("审理法院")
        res_dic["审理法院"] = get_court_code_by_case_number(param)["法院名称"]
    res = call_api(url, param)
    if isinstance(res, dict) and res:
        res.update(res_dic)
        if res:
            li = [f"使用 {param} 查询结果: {res}"]
        else:
            return []
        for k, v in res.items():
            li.append({"实体": v, "格式匹配为": dic.get(k, k)})

        return li
    elif task_dic["表名"] in ["XzgxfInfo", "LegalDoc"]:
        if "(" in task_dic["实体"]["案号"] or ")" in task_dic["实体"]["案号"]:
            task_dic["实体"]["案号"] = task_dic["实体"]["案号"].replace("(", "（").replace(")", "）")
            return do_task(task_dic, depth + 1)
        elif "（" in task_dic["实体"]["案号"] or "）" in task_dic["实体"]["案号"]:
            task_dic["实体"]["案号"] = task_dic["实体"]["案号"].replace("（", "(").replace("）", ")")
            return do_task(task_dic, depth + 1)
        elif "【" in task_dic["实体"]["案号"] or "】" in task_dic["实体"]["案号"]:
            task_dic["实体"]["案号"] = task_dic["实体"]["案号"].replace("【", "(").replace("】", ")")
            return do_task(task_dic, depth + 1)
    elif need_fields:
        flow = [
            {
                "step": 1,
                "goal": f"根据{task_dic['实体']}查询{need_fields}",
                "type": "查询",
                "suggestion": f"使用 {url} 接口 传入参数 {param}",
                "table_name": task_dic["表名"],
                "is_necessary": "necessary",
                "base_on_step": [0],
            }
        ]
        executor = Executor(f"根据{task_dic['实体']}查询{task_dic['需要字段']}", flow, max_try_num=1)
        executor.handle_one_step(flow[0])
        out = executor.code_kernel.cache_code_list[-1]["out"]

        executor.code_kernel.shutdown()
        for res in out:
            if "查询结果为:" in res:
                return [res]
    return []


def hashable(item):
    """将不可哈希的元素（如字典）转换为可哈希的形式"""
    if isinstance(item, dict):
        return frozenset((k, hashable(v)) for k, v in item.items())
    elif isinstance(item, list):
        return tuple(hashable(i) for i in item)
    elif isinstance(item, set):
        return frozenset(hashable(i) for i in item)
    return item


def deduplicate(lst):
    seen = set()
    result = []
    for item in lst:
        h_item = hashable(item)
        if h_item not in seen:
            seen.add(h_item)
            result.append(item)
    return result


def preprocess_question(question, ner, history=None, depth=0):
    if depth > 5:
        return {"type": "查询达到最大深度", "question": question, "history": history}
    if history is None:
        history = question_entity_processing(question, ner)
        if re.search("小数|亿|子公司|最高|最低|第一|第二|第三|总.?额|次数|区划代码|度", question):
            return {"type": "任务未完成", "question": question, "history": history}
    pos_table = []
    for table in TABLES:
        if isinstance(table["key"][0], str):
            for entity in history:
                if isinstance(entity, dict):
                    if entity["格式匹配为"] in table["key"]:
                        pos_table.append(table)
                        break
        elif isinstance(table["key"][0], set):
            if set([i["格式匹配为"] for i in history if isinstance(i, dict)]) & table["key"][0] == table["key"][0]:
                pos_table.append(table)
    json_format_1 = """
{
"任务是否完成":true/false,
"是否还有直接查询":true/false,
"任务列表":[{
"实体":{"key":"values"},"表名":"TableName","需要字段":["xxx","xxx"],
"实体":{"key":"values"},"表名":"TableName","需要字段":["xxx","xxx"],
}]
}    
"""
    sample = """
问题为：(2021)豫0302知民初616号的原告是谁，它是哪个行业的,
查询为：{"名称": "(2021)豫0302知民初616号", "格式匹配为": "案号"}
使用 {"query_conds": {"案号": "(2021)豫0302知民初616号"}, "need_fields": ["原告", "案号", "案号"]} 查询结果: {"原告": "宇通客车股份有限公司", "案号": "(2021)豫0302知民初616号"}    
结果：```json
{
"任务是否完成": false,
"是否还有直接查询": true, // 检测到可以从查询中继续进行的结果
"任务列表":[{
  "实体": {"公司名称": "宇通客车股份有限公司"}, 
  "表名": "CompanyRegister", 
  "需要字段": ["行业一级","行业二级","行业三级"]
}]
}   
```

问题：91110114MA01FJUP7F这家公司有多少子公司
查询：使用 {"query_conds": {"统一社会信用代码": "91110114MA01FJUP7F"}, "need_fields": []} 查询结果:{"实体": "北京弘进久安生物科技有限公司", "格式匹配为": "公司名称"}
结果：```json
{
"任务是否完成": false,
"是否还有直接查询": false, // 不需要查询子公司
"任务列表":[]
}
```

问题为：我想了解四川鑫达新能源科技有限公司涉及的案件中，起诉时间发生于2020年发生的民事初审案件有几次？案号分别是？,
查询为：{'名称': '四川鑫达新能源科技有限公司', '格式匹配为': '公司名称'}
{'名称': '2020年', '格式匹配为': '日期'}
使用 {'query_conds': {'公司名称': '四川鑫达新能源科技有限公司'}, 'need_fields': ['公司名称', '公司名称']} 查询结果: {'公司名称': '四川鑫达新能源科技有限公司'}
```json
{
"任务是否完成": false,
"是否还有直接查询": false, // 涉案无需查询
"任务列表":[]
}
```

问题为：湘潭电机物流有限公司的成立时间和注册金额是多少万元？如果该公司被限高了，最大的涉案金额为？该案件的案号为？
查询：[湘潭电机物流有限公司]
```json
{
"任务是否完成": false,
"是否还有直接查询": true, // 可以直接从表中获取成立时间和注册金额
"任务列表":[{
  "实体": {"公司名称": "湘潭电机物流有限公司"}, 
  "表名": "CompanyRegister", 
  "需要字段": ["成立日期","注册资本"]
}]
}
```

问题为：北京市海淀区人民法院的法院级别是什么
查询：[法院名称：北京市海淀区人民法院]
```json
{
"任务是否完成": false,
"是否还有直接查询": true, // 可以直接从表中获取成立时间和注册金额
"任务列表":[{
  "实体": {"法院名称": "北京市海淀区人民法院"}, 
  "表名": "CourtCode", 
  "需要字段": ["法院级别"]
}]
}
```

问题为：湘潭电机物流有限公司的成立时间和注册金额是多少万元？如果该公司被限高了，最大的涉案金额为？该案件的案号为？
查询：使用 {"query_conds": {"公司名称": "湘潭电机物流有限公司"}, "need_fields": ["成立日期", "注册资本", "公司名称"]} 查询结果:{"实体": "2000-01-06", "格式匹配为": "成立日期"}{"实体": "1000", "格式匹配为": "注册资本"}{"实体": "湘潭电机物流有限公司", "格式匹配为": "公司名称"}
```json
{
"任务是否完成": false,
"是否还有直接查询": false, // 不需要查询限高，成立时间和注册金额已完成
"任务列表":[]
}
```

2020年1月4日这一天,这个地址的北京市海淀区清华东路9号创达大厦5层506室的天气如何?其最高温度和最低温度分别是多少?然后在帮我查下这个地址的区县名称以及他的区县区划代码?,
为了解决问题我做出来如下查询：
使用 {"query_conds": {"地址": "北京市海淀区清华东路9号创达大厦5层506室"}, "need_fields": []} 查询结果:{"名称": "2020年1月4日", "格式匹配为": "日期"}{"实体": "北京市海淀区清华东路9号创达大厦5层506室", "格式匹配为": "地址"}{"实体": "北京市", "格式匹配为": "省份"}{"实体": "北京市", "格式匹配为": "城市"}{"实体": "海淀区", "格式匹配为": "区县"}
可以查询的表名为：
[{"表名": "AddressInfo", "属性值": ["地址", "省份", "城市", "区县"], "key": ["地址"], "作用": "通过地址查询省市区，查询后的结果可以用于查询天气和区划代码"}, {"表名": "AddressrCode", "属性值": ["省份", "城市", "城市区划代码", "区县", "区县区划代码"], "key": [{"城市", "省份", "区县"}], "作用": "通过省份，城市，区县三个字段查询区划代码"}, {"表名": "TempInfo", "属性值": ["日期", "省份", "城市", "天气", "最高温度", "最低温度", "湿度"], "key": [{"城市", "省份", "日期"}], "作用": "通过日期省份城市查询天气"}]
```json
{
"任务是否完成": false,
"是否还有直接查询": true,
"任务列表":[{
  "实体": {"省份": "北京市","城市": "北京市",  "日期":"2020年1月4日"}, 
  "表名": "TempInfo", 
  "需要字段": ["日期", "天气", "最高温度", "最低温度"]
},{
  "实体": {"省份": "北京市","城市": "北京市",  "区县":"海淀区"}, 
  "表名": "AddressCode", 
  "需要字段": ["区县区划代码"]
}]```

题目：原告300006案件，即重庆莱美药业股份有限公司作为原告的案件，审理法院为重庆市南岸区人民法院。重庆市南岸区人民法院的成立日期为[未知]。
使用 {"query_conds": {"法院名称": "重庆市南岸区人民法院"}, "need_fields": ["成立日期", "法院名称"]} 查询结果:", {"实体": "-", "格式匹配为": "成立日期"}, {"实体": "重庆市南岸区人民法院", "格式匹配为": "法院名称"}
```json
{
"任务是否完成": true, // 备注 查询到 - 也算查询到
"是否还有直接查询": true,
"任务列表":[]
}
```

问题为：(2019)川01民初4929号案件中，审理当天原告的律师事务所与被告的律师事务所所在地区的最高温度相差多少度？,
查询为：{"名称": "(2019)川01民初4929号", "格式匹配为": "案号"}
使用 {"query_conds": {"案号": "(2019)川01民初4929号"}, "need_fields": ["原告律师事务所", "被告律师事务所", "日期", "案号"]} 查询结果: {"原告律师事务所": "四川力久律师事务所", "被告律师事务所": "重庆强知大律师事务所", "日期": "2019-12-11 00:00:00", "案号": "(2019)川01民初4929号"}
```json
{
"任务是否完成": false,
"是否还有直接查询": true,
"任务列表":[{
  "实体": {"律师事务所名称": "四川力久律师事务所"}, 
  "表名": "LawfirmInfo", 
  "需要字段": ["律师事务所地址"]
},{
  "实体": {"律师事务所名称": "重庆强知大律师事务所"}, 
  "表名": "LawfirmInfo", 
  "需要字段": ["律师事务所地址"]
}]  // 你只需要考虑实体，不要做任何推理，不要推理出省市区，除非查询出来。
}
```
问题为：(2023)津0116执29434号的被申请人一共有多少家子公司。
查询为：{'名称': '(2023)津0116执29434号', '格式匹配为': '案号'}
```json
{
"任务是否完成": false,
"是否还有直接查询": true,
"任务列表":[{
  "实体": {"案号": "(2023)津0116执29434号"}, 
  "表名": "LegalDocument", 
  "需要字段": ["被告"]
}]
}

"""
    prompt = f"""
你需要根据给定的信息判断任务是否完成，并确定是否还有直接查询任务。如果任务未完成且还有直接查询任务，请将其转换为任务列表。
注意事项：
直接查询是指使用表格的 key 直接获取特定的属性值。
以下查询不属于直接查询：
    1.查询子公司
    2.查询公司涉案情况
    3.查询公司限制高消费情况
如果遇到上述情况，直接查询应填写为 false。
备注：实体字段的key和value不要做任何改变
例如：x公司的子公司是？x公司的涉案情况？都不是直接查询遇到以上几种情况，直接查询填false
查询天气区划代码时，需要先查询地址，然后查询AddrInfo最后查询天气和区划代码，天气记得查询日期

按照以下json格式输出:
```json
{json_format_1}
```

示例：
{sample}
---示例结束--
你不需要计划以后需要做什么，我会指导你一步步做，你只需要把当前能够查询到的列举出来就可以了。
你也无需查找已知内容，例如查询结果已有的内容和公司名称
不要出现指代的实体，例如：原告律师事务所，原告公司这样的指代不要出现，你的task会被执行，不要传递错误参数。
你填到task里的任务都是有具体名称的，只有本步骤能执行。另外只考虑我给你的表格，不要参考示例表格。
仅仅输出当前能执行的json和状态信息,另外之前已经查询到的无需再次查询,结果在```json ``` 内。
"""

    task_list_dict = llm_eval(
        [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"""你本次只能从以下表格中查询：
{pos_table}
请开始分析：
问题为：{question},
查询为：{format_history(history)}
你的json:""",
            },
        ]
    )

    last_step = len(history)
    if task_list_dict["任务是否完成"]:
        if re.search("小数|亿|万", question):
            return {"type": "任务未完成", "question": question, "history": history}
        else:
            return {"type": "任务完成", "question": question, "history": history}
    elif task_list_dict["是否还有直接查询"]:
        for task in task_list_dict["任务列表"]:
            history.extend(do_task(task))
        history = deduplicate(history)
        if len(history) == last_step:
            return {"type": "任务未完成", "question": question, "history": history}
        return preprocess_question(question, ner, history, depth + 1)
    else:
        return {"type": "任务未完成", "question": question, "history": history}


def get_new_question(question, answer):
    prompt = """
以下是一些解决了一半的题目。
结果中有一些地方是未知的，帮我根据未知提出新的问题。
如果题目完全没有被回答，则返回：解答失败。
如果有内容更新，则提出新的问题.

以下是几个回答示例，解答完整参考此示例：
示例：
题目：请问(2019）鲁0991执保239号的上诉人和被诉人分别是？
答案：(2019）鲁0991执保239号案件的上诉人和被诉人信息目前未知。
新的问题:解答失败

问题：阿拉尔新农乳业有限责任公司的历史涉诉案件中，聘用律师事务所的负责人分别是？这些事务所分布在哪些城市？
答案：阿拉尔新农乳业有限责任公司的历史涉诉案件中，涉及到的律师事务所及其负责人如下：河北冀秦律师事务所的负责人是[未知]，新疆天澈律师事务所的负责人是[未知]，北京大成（乌鲁木齐）律师事务所的负责人是[未知]，新疆天沃律师事务所的负责人是[未知]。这些律师事务所所在的城市信息目前无法得知。
新的问题：`河北冀秦律师事务所`,`新疆天澈律师事务所`，`北京大成（乌鲁木齐）律师事务所`，`新疆天沃律师事务所`的地址和负责人是？

问题：案件(2020)闽01民终3323号的原告师事务所所在的城市区划代码是多少，
答案：案件(2020)闽01民终3323号的原告律师事务所为福建坤广律师事务所。根据查询到的信息，福建坤广律师事务所的地址位于福州市晋安区华林路338号龙赋大厦东区6楼。但是，查询结果中并未提供福州市晋安区的城市区划代码，因此该信息为[未知]
新的问题:`福州市晋安区华林路338号龙赋大厦东区6楼所`在城市的城市区划代码是什么？

问题：91411625MA40GA2H02这家公司的母公司一共有多少家子公司
答案：91411625MA40GA2H02这家公司的母公司河南金丹乳酸科技股份有限公司的子公司数量为[未知]。
新的问题:河南金丹乳酸科技股份有限公司的子公司数量为多少？

你一定要使用我给你的已知条件里的字段，不要添加任何推理，字段使用 ``。
"""
    question_flow = [{"role": "system", "content": prompt}]
    question_flow.append(
        {
            "role": "user",
            "content": f"""问题：{question}，答案：{answer}。
新的问题(仅输出问题):""",
        }
    )
    new_question = llm(question_flow)

    return new_question
