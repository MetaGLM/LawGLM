import json
import ast
from typing import get_origin, Annotated


from model import call_glm
from match_tools.tools_register import register_tool
from match_tools.schema import get_table_properties, get_table_property_list
from apis.api import augment_company_name, http_api_call_original, http_api_call
from utils import parse_json_from_response

refine_company_prompt = """有两张表，一张是company_table_1，包含的字段有：公司名称, 公司简称, 英文名称, 关联证券, 公司代码_股票代码, 曾用简称, 所属市场, 所属行业, 成立日期, 上市日期, 法人代表, 总经理 ,董秘, 邮政编码, 注册地址, 办公地址, 联系电话, 传真, 官方网址, 电子邮箱, 入选指数, 主营业务, 经营范围, 机构简介, 每股面值, 首发价, 首发募资净额, 首发主承销商。
另一张是company_table_2，包含的字段有：公司名称, 登记状态, 统一社会信用代码, 法定代表人, 注册资本, 成立日期, 企业地址, 联系电话, 联系邮箱, 注册号, 组织机构代码, 参保人数, 行业一级, 行业二级, 行业三级, 曾用名, 企业简介,经营范围。

请根据原始问题和已知信息判断出问题中需要用到上述两张表的哪些字段。
要注意有时候问题所涉及到信息和表中字段不完全相同但是语义相近，要自动转成语义相近的字段。比如问题涉及'法人信息'可以转成字段中的'法人代表'或'法定代表人'。
返回的结果放在dict中，键table表示用到哪张表，键property表示用到哪些字段，如果是上市公司基本信息表还需要用到键args表示搜索该表的参数有'公司名称'和'公司代码'两个选项，其中公司代码也是股票代码由6个数字组成,args的格式是dict,它的key是'公司名称'和'公司代码'其中一个,value是公司名称或者公司代码具体内容。
如果无法确认原始问题中后续逻辑链(子问题)需要用到表中的具体哪些字段，那么可以把键property的值设置成空数组，表示查询整张表。

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙龙元建设集团股份有限公司的法人信息与总经理是否相同？
```json
{{"table":"上市公司基本信息表","property":["法人代表","总经理"],"args":{{"公司名称":"龙元建设集团股份有限公司"}}}}
``` 

example：与公司代码为301012有关联的案件审理法院的级别是什么
```json
{{"table":"company_table_1","property":["公司名称"],"args":{{"公司代码":"301012"}}
``` 

example：安徽安科恒益药业有限公司注册地址所在区县是
```json
{{"table":"company_table_2","property":["企业地址"],"args":{{"公司名称":"安徽安科恒益药业有限公司"}}
``` 

由于原始问题比较复杂，需要进行多跳查询。所以你在分析问题时要根据'已知信息'判断目前进到哪一步查询了，如果没有提供'已知信息'那么表示问题刚开始进行查询只要返回最前面的逻辑链需要得到上述两张表的信息，而不需要考虑原始问题后面逻辑链(子问题)所用到的上述两张表的信息。如果有已知信息表示已经开始了原始问题的逻辑链，只要考虑原始问题当前逻辑链后面的最近的逻辑链(子问题)所用到的上述两张表的信息。
根据目前执行的逻辑链只返回后面紧接着的逻辑链(子问题)所用到的上述两张表的信息，并且每次只返回其中一张表。
比如下面的例子中通过已知信息知道目前原始问题的逻辑链走到知道上市公司名称，后就紧接着要处理的逻辑链(子问题)是'是否为上市公司，如果是的话，他的股票代码和上市日期分别是？'
example：(2019)冀01民终10768号的被申请人是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？
已知信息：(2019)冀01民终10768号的申请人是石家庄越融担保有限公司
```json
{{"table":"company_table_1","property":["公司代码_股票代码","上市日期"],"args":{{"公司名称":"石家庄越融担保有限公司"}}}}
``` 

下面的例子中通过已知信息知道目前原始问题的逻辑链走到知道上市公司名称并且不是上市公司，那么后就紧接着要处理的逻辑链(子问题)是'如果不是的话，统一社会信用代码是？'
example：(2019)冀01民终10768号的被申请人是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？
已知信息：(2019)冀01民终10768号的申请人是石家庄越融担保有限公司。石家庄越融担保有限公司不是上市公司。
```json
{{"table":"company_table_2","property":["统一社会信用代码"]}}
``` 

对于两张表中相同或相似的字段信息，要从上市公司基本信息表获取
example：请帮我查一下南京聚隆科技股份有限公司的法定代表人和统一社会代码分别是?
```json
{{"table":"company_table_1","property":["法人代表"],"args":{{"公司名称":"南京聚隆科技股份有限公司"}}}}
``` 

example：请帮我查一下南京聚隆科技股份有限公司的法定代表人和统一社会代码分别是?
已知信息：南京聚隆科技股份有限公司的法定代表人是张三。
```json
{{"table":"company_table_2","property":["统一社会信用代码"]}}
``` 

<原始问题>
{query}
</原始问题>

{provided_information}
"""

tool_name_map = {"company_table_1": "get_company_info", "company_table_2": "get_company_register"}


def pre_process_company_tools(tool_name, args, message, logic_chain, query):
    if tool_name in ["get_company_info", "get_company_register"]:
        try:
            if logic_chain:
                provided_information = "\n".join(logic_chain)
                provided_information = "<已知信息>\n" + provided_information + "\n</已知信息>\n"
            else:
                provided_information = ""
            prompt = refine_company_prompt.format(query=query, provided_information=provided_information)
            messages = [{"role": "user", "content": prompt}]
            response = call_glm(messages, model="glm-4-0520")
            refined_tool = parse_json_from_response(response.choices[0].message.content)
            refined_tool_name = tool_name_map.get(refined_tool.get("table", ""), "")

            dict_args = json.loads(args)
            old_company_name, old_company_id = "", ""
            if tool_name == "get_company_register" and dict_args.get("company_name", ""):
                old_company_name = dict_args.get("company_name")
            if tool_name == "get_company_info" and dict_args.get("value", ""):
                if dict_args.get("key", "").__contains__("代码"):
                    old_company_id = dict_args.get("value", "")
                else:
                    old_company_name = dict_args.get("value", "")

            refined_args = {}
            refined_args["target_property"] = refined_tool.get("property", [])
            if refined_tool_name == "get_company_register":
                refined_args["company_name"] = old_company_name
            elif refined_tool_name == "get_company_info":
                if type(refined_tool.get("args", "")) == dict and refined_tool.get("args").get("公司名称", ""):
                    refined_args["key"] = "公司名称"
                    refined_args["value"] = (
                        old_company_name if old_company_name else refined_tool.get("args").get("公司名称", "")
                    )
                elif type(refined_tool.get("args", "")) == dict and refined_tool.get("args").get("公司代码", ""):
                    refined_args["key"] = "公司代码"
                    refined_args["value"] = (
                        old_company_id if old_company_id else refined_tool.get("args").get("公司代码", "")
                    )

            refined_args = json.dumps(refined_args, ensure_ascii=False)

            if (
                "tool_calls" in message.keys()
                and type(message["tool_calls"]) == list
                and len(message["tool_calls"]) == 1
            ):
                if (
                    type(message["tool_calls"][0]) == dict
                    and "function" in message["tool_calls"][0].keys()
                    and "name" in message["tool_calls"][0]["function"].keys()
                    and "arguments" in message["tool_calls"][0]["function"].keys()
                ):
                    message["tool_calls"][0]["function"]["name"] = refined_tool_name
                    message["tool_calls"][0]["function"]["arguments"] = refined_args

            return refined_tool_name, refined_args, message
        except Exception as e:
            return tool_name, args, message
            pass
    return tool_name, args, message


def check_tool_and_args(tool_name, args, message, logic_chain, query):
    args_json = json.loads(args)
    if args_json.get("target_property", []):
        target_property = args_json.get("target_property", [])
        if tool_name == "get_company_info":
            table_properties = get_table_property_list("company_info")
            correct_args, incorrect_args = [], []
            for property in target_property:
                if property in table_properties:
                    correct_args.append(property)
                else:
                    incorrect_args.append(property)
            if len(incorrect_args) == 0:
                return tool_name, args
            if len(correct_args) > 0 and target_property[0] in correct_args:
                target_property = correct_args
                args_json["target_property"] = target_property
                return tool_name, json.dumps(args_json, ensure_ascii=False)
            else:
                if not args_json.get("key", "").__contains__("代码") and args_json.get("value", ""):
                    table_properties = get_table_property_list("company_register")
                    correct_args, incorrect_args = [], []
                    for property in target_property:
                        if property in table_properties:
                            correct_args.append(property)
                        else:
                            incorrect_args.append(property)
                    if len(correct_args) > 0:
                        return "get_company_register", json.dumps(
                            {"company_name": args_json.get("value", ""), "target_property": correct_args},
                            ensure_ascii=False,
                        )

        elif tool_name == "get_company_register":
            table_properties = get_table_property_list("company_register")
            correct_args, incorrect_args = [], []
            for property in target_property:
                if property in table_properties:
                    correct_args.append(property)
                else:
                    incorrect_args.append(property)
            if len(incorrect_args) == 0:
                return tool_name, args
            if len(correct_args) > 0 and target_property[0] in correct_args:
                target_property = correct_args
                args_json["target_property"] = target_property
                return tool_name, json.dumps(args_json, ensure_ascii=False)
            else:
                table_properties = get_table_property_list("company_info")
                correct_args, incorrect_args = [], []
                for property in target_property:
                    if property in table_properties:
                        correct_args.append(property)
                    else:
                        incorrect_args.append(property)
                if len(correct_args) > 0:
                    return "get_company_info", json.dumps(
                        {
                            "key": "公司名称",
                            "value": args_json.get(
                                "company_name",
                            ),
                            "target_property": correct_args,
                        },
                        ensure_ascii=False,
                    )
    return tool_name, args
