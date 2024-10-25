from LLM import LLM
from LLM import LLMs_tools
from prompt import *
from tools_class import *
from utils import convert_date_format
import re


EXAMPLE = {
    "公民起诉公民": {
        "原告": "张三",
        "原告性别": "男",
        "原告生日": "1976-10-2",
        "原告民族": "汉",
        "原告工作单位": "XXX",
        "原告地址": "中国",
        "原告联系方式": "123456",
        "原告委托诉讼代理人": "李四",
        "原告委托诉讼代理人联系方式": "421313",
        "被告": "王五",
        "被告性别": "女",
        "被告生日": "1975-02-12",
        "被告民族": "汉",
        "被告工作单位": "YYY",
        "被告地址": "江苏",
        "被告联系方式": "56354321",
        "被告委托诉讼代理人": "赵六",
        "被告委托诉讼代理人联系方式": "09765213",
        "诉讼请求": "AA纠纷",
        "事实和理由": "上诉",
        "证据": "PPPPP",
        "法院名称": "最高法",
        "起诉日期": "2012-09-08",
    },
    "公司起诉公民": {
        "原告": "上海公司",
        "原告地址": "上海",
        "原告法定代表人": "张三",
        "原告联系方式": "872638",
        "原告委托诉讼代理人": "B律师事务所",
        "原告委托诉讼代理人联系方式": "5678900",
        "被告": "王五",
        "被告性别": "女",
        "被告生日": "1975-02-12",
        "被告民族": "汉",
        "被告工作单位": "YYY",
        "被告地址": "江苏",
        "被告联系方式": "56354321",
        "被告委托诉讼代理人": "赵六",
        "被告委托诉讼代理人联系方式": "09765213",
        "诉讼请求": "AA纠纷",
        "事实和理由": "上诉",
        "证据": "PPPPP",
        "法院名称": "最高法",
        "起诉日期": "2012-09-08",
    },
    "公民起诉公司": {
        "原告": "张三",
        "原告性别": "男",
        "原告生日": "1976-10-2",
        "原告民族": "汉",
        "原告工作单位": "XXX",
        "原告地址": "中国",
        "原告联系方式": "123456",
        "原告委托诉讼代理人": "李四",
        "原告委托诉讼代理人联系方式": "421313",
        "被告": "王五公司",
        "被告地址": "公司地址",
        "被告法定代表人": "赵四",
        "被告联系方式": "98766543",
        "被告委托诉讼代理人": "C律师事务所",
        "被告委托诉讼代理人联系方式": "425673398",
        "诉讼请求": "AA纠纷",
        "事实和理由": "上诉",
        "证据": "PPPPP",
        "法院名称": "最高法",
        "起诉日期": "2012-09-08",
    },
    "公司起诉公司": {
        "原告": "上海公司",
        "原告地址": "上海",
        "原告法定代表人": "张三",
        "原告联系方式": "872638",
        "原告委托诉讼代理人": "B律师事务所",
        "原告委托诉讼代理人联系方式": "5678900",
        "被告": "王五公司",
        "被告地址": "公司地址",
        "被告法定代表人": "赵四",
        "被告联系方式": "98766543",
        "被告委托诉讼代理人": "C律师事务所",
        "被告委托诉讼代理人联系方式": "425673398",
        "诉讼请求": "AA纠纷",
        "事实和理由": "上诉",
        "证据": "PPPPP",
        "法院名称": "最高法",
        "起诉日期": "2012-09-08",
    },
}

API_NAME = {
    "公民起诉公民": "get_citizens_sue_citizens",
    "公司起诉公民": "get_company_sue_citizens",
    "公民起诉公司": "get_citizens_sue_company",
    "公司起诉公司": "get_company_sue_company",
}

table_info_prompt = """###数据表信息如下：
上市公司基本信息表（CompanyInfo）有下列字段：
['公司名称', '公司简称', '英文名称', '关联证券', '公司代码', '曾用简称', '所属市场', '所属行业', '成立日期', '上市日期', '法人代表', '总经理', '董秘', '邮政编码', '注册地址', '办公地址', '联系电话', '传真', '官方网址', '电子邮箱', '入选指数', '主营业务', '经营范围', '机构简介', '每股面值', '首发价格', '首发募资净额', '首发主承销商']
-------------------------------------
公司工商照面信息表（名称: CompanyRegister）有下列字段：
["公司名称", "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "企业简介", "经营范围"]
-------------------------------------
律师事务所信息表（名录）（LawfirmInfo）有下列字段：
['律师事务所名称', '律师事务所唯一编码', '律师事务所负责人', '事务所注册资本', '事务所成立日期', '律师事务所地址', '通讯电话', '通讯邮箱', '律所登记机关']
"""

table_info_prompts = [
    """###数据表信息如下：
上市公司基本信息表（CompanyInfo）有下列字段：
['公司名称', '公司简称', '英文名称', '关联证券', '公司代码', '曾用简称', '所属市场', '所属行业', '成立日期', '上市日期', '法人代表', '总经理', '董秘', '邮政编码', '注册地址', '办公地址', '联系电话', '传真', '官方网址', '电子邮箱', '入选指数', '主营业务', '经营范围', '机构简介', '每股面值', '首发价格', '首发募资净额', '首发主承销商']
""",
    """数据表信息如下：
公司工商照面信息表（名称: CompanyRegister）有下列字段：
["公司名称", "登记状态", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "企业地址", "联系电话", "联系邮箱", "注册号", "组织机构代码", "参保人数", "行业一级", "行业二级", "行业三级", "曾用名", "企业简介", "经营范围"]
""",
    """数据表信息如下：
律师事务所信息表（名录）（LawfirmInfo）有下列字段：
['律师事务所名称', '律师事务所唯一编码', '律师事务所负责人', '事务所注册资本', '事务所成立日期', '律师事务所地址', '通讯电话', '通讯邮箱', '律所登记机关']
""",
]


def produce_args(question_type, information, question, template):
    if question_type.find("公民") == -1:
        for key in template:
            template[key] = ""
        prompt = f"""
根据提供的信息{information}，请解决该问题：{question}，注意对于key=="地址"，需要将所有查到的地址都拼接起来作为value，对于key=="联系方式"，需要将所有查到的联系电话都拼接起来作为value，对于诉讼代理人，最好将律师事务所负责人和事务所名称拼接起来作为value，最终严格按照以下json格式进行输出，可以被Python json.loads函数解析：
```json
{{
    {template}
}}
```"""
    else:
        for key in template:
            template[key] = ""
        prompt = f"""
根据提供的信息{information}，请解决该问题：{question}，注意对于key=="地址"，将所有地址拼接作为value，对于key=="联系方式"，需要将所有查到的联系电话都拼接起来作为value，对于诉讼代理人，将律师事务所负责人和事务所名称拼接起来作为value，对于诉讼请求，将提供信息中发生的纠纷作为value。对于诉讼方为公民身份的，其地址电话可用公司的代替，而当某些key（如性别、生日、民族等）没有相应信息时，以"空"为value。最终严格按照以下json格式进行输出（所有字段都需要保留，不能缺省），可以被Python json.loads函数解析：
```json
{{
    {template}
}}
```"""
    return prompt


def find_substring_indexes(text, pattern):
    # Use the finditer method to find all matches and their positions
    matches = re.finditer(pattern, text)

    # Extract the start position of each match
    indexes = [match.start() for match in matches]

    return indexes


def process_sue(question):
    # 1. 分类
    question_type = ""
    try:
        response = LLM(TYPE_CLASS.format(question=question.split("，")[0]))  # 简化问题，删去对于本步没用的冗余信息
        question_type = prase_json_from_response(response)["类型"]
        if question_type not in API_NAME.keys():
            question_type = "公司起诉公司"
    except:
        indexes1 = find_substring_indexes(question.split("民事起诉状")[0], "法人")
        indexes2 = find_substring_indexes(question.split("民事起诉状")[0], "公司")
        if len(indexes1) >= 2:
            question_type = "公民起诉公民"
        elif len(indexes1) == 1 and len(indexes2) >= 2:
            if indexes1[0] > indexes2[0] and indexes1[0] < indexes2[1]:
                question_type = "公民起诉公司"
            elif indexes1[0] > indexes2[1]:
                question_type = "公司起诉公民"
            else:
                question_type = "公司起诉公司"
        else:
            question_type = "公司起诉公司"
    # 2. 根据类别匹配模版
    template = EXAMPLE[question_type]
    # 3. 检索信息, [公司1的上市，公司1的注册，公司2的上市，公司2的注册]
    information = []
    try:
        response = LLM(PRODUCE_WORD_PROMPT[0].format(question=("，").join(question.split("，")[0:3])))
        plan = prase_json_from_response(response)
        for step, subplan in enumerate(plan):
            if step == 0 or step == 2:
                query = subplan["问题"] + table_info_prompts[0]
                used_tools = [register_tool_one(get_company_info)]
            elif step == 1 or step == 3:
                query = subplan["问题"] + table_info_prompts[1]
                used_tools = [register_tool_one(get_company_register)]
            else:
                query = subplan["问题"] + table_info_prompts[2]
                used_tools = [register_tool_one(get_lawfirm_info)]
            api_name, api_args = LLMs_tools(query, used_tools)
            if isinstance(api_args["need_fields"], dict):
                api_args["need_fields"] = list(api_args["need_fields"].values())[0]
            if isinstance(api_args["need_fields"], list) == False:
                api_args["need_fields"] = []
            ori_answer = http_api_call(api_name=api_name, data=api_args)
            information.append(ori_answer["输出结果"][0])
        assert len(information) == 6
    except:
        information = []
        company_names = (
            LLM(f"提取问题中的有限公司名称，问题：{question}，只输出公司名称，如果有多个，以,分隔")
        ).split(",")[:2]
        lawfirm_names = (
            LLM(f"提取问题中的律师事务所名称，问题：{question}，只输出律师事务所，如果有多个，以,分隔")
        ).split(",")[:2]
        for company_name in company_names:
            api_name = "get_company_info"
            api_args = {
                "need_fields": ["法人代表", "注册地址", "办公地址", "联系电话"],
                "query_conds": {"公司名称": company_name},
            }
            ori_answer = http_api_call(api_name=api_name, data=api_args)
            if ori_answer["输出结果总长度"] != 0:
                information.append(ori_answer["输出结果"][0])
            api_name = "get_company_register"
            api_args = {"need_fields": ["企业地址", "联系电话"], "query_conds": {"公司名称": company_name}}
            ori_answer = http_api_call(api_name=api_name, data=api_args)
            if ori_answer["输出结果总长度"] != 0:
                information.append(ori_answer["输出结果"][0])
        for lawfirm_name in lawfirm_names:
            api_name = "get_lawfirm_info"
            api_args = {
                "need_fields": ["律师事务所负责人", "通讯电话"],
                "query_conds": {"律师事务所名称": lawfirm_name},
            }
            ori_answer = http_api_call(api_name=api_name, data=api_args)
            if ori_answer["输出结果总长度"] != 0:
                information.append(ori_answer["输出结果"][0])
    # 4. 处理信息

    prompt = produce_args(question_type=question_type, information=information, question=question, template=template)
    args = prase_json_from_response(LLM(prompt))

    # 特殊处理一些key
    try:
        for key in args:
            if key == "原告地址":
                addr = set()
                addr.add(information[0]["注册地址"])
                addr.add(information[0]["办公地址"])
                addr.add(information[1]["企业地址"])
                args[key] = (", ").join(addr)
            if key == "被告地址":
                addr = set()
                addr.add(information[2]["注册地址"])
                addr.add(information[2]["办公地址"])
                addr.add(information[3]["企业地址"])
                args[key] = (", ").join(addr)
            if key == "原告生日":
                args["原告工作单位"] = args["原告"]
                args["原告"] = information[0]["法人代表"]
            if key == "被告生日":
                args["被告工作单位"] = args["被告"]
                args["被告"] = information[2]["法人代表"]
    except:
        pass

    # 5. 生成得到文书
    api_name = API_NAME[question_type]
    res = http_api_call(api_name=api_name, data=args)

    answer = res["输出结果"]
    answer = convert_date_format(answer, 1)

    return answer
