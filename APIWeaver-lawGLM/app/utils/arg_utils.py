import re
from knowledge.api_info import APIS
from copy import deepcopy
from datetime import datetime

API_DICT = {}
for api in APIS:
    d = deepcopy(api)
    example = d["返回值示例"]
    if isinstance(example, dict):
        d["可选need_fields字段"] = list(example.keys())
    elif isinstance(example, list) and example and isinstance(example[0], dict):
        d["可选need_fields字段"] = list(example[0].keys())
    else:
        d["可选need_fields字段"] = []
    del d["返回值示例"]
    API_DICT[d["路由"]] = d


def string2eval(input_string):
    pattern = r"(\{'query_conds': \{'.+?':\s{0,2})([^']+)(\},\s?'need_fields': \[.*?\]\})"

    # 替换函数
    def replace_match(match):
        return match.group(1) + '"' + match.group(2) + '"' + match.group(3)

    # 进行替换
    output_string = re.sub(pattern, replace_match, input_string)

    # 输出结果
    return output_string


def check_suggestion(suggestion):
    suggestion_back = ""
    interface = re.findall("/[a-z_]+", suggestion)
    if interface:
        interface = interface[0]
        if interface not in API_DICT:
            return f"{interface} 路由不存在，如果你使用的是推荐的函数，请不要使用路由格式，直接说 使用函数：function_name,传入参数xxx"

        param = re.split("参数.{0,2}\{", suggestion)
        if len(param) == 2:
            api_info = API_DICT[interface]
            end_inx = 0
            for inx, char in enumerate(param[1]):
                if char == "}":
                    end_inx = inx
            try:
                param = eval(string2eval("{" + param[1][:end_inx] + "}"))
                return validate_params(interface, param, api_info)
            except:
                # print(string2eval('{' + param[1][:end_inx] + '}'))
                # print(f'`{suggestion}`无法校验')
                return ""
    return suggestion_back.strip()


def validate_params(interface, param, api_info):
    suggestion_back = ""
    required_keys = {"query_conds", "need_fields"}
    if not required_keys <= param.keys():
        return f"{interface} 的参数 {param} 错误，需要query_conds 和 need_fields 字段"

    query_conds_keys = list(param["query_conds"].keys())
    need_fields = param["need_fields"]
    pos_key = list(api_info["输入参数"]["query_conds"].keys())[0].split("|")

    if interface == "/get_address_code":
        if set(query_conds_keys) != {"省份", "城市", "区县"}:
            return f'/get_address_code 接口格式为 {{"query_conds": {{"省份": "str", "城市": "str", "区县": "str"}}, "need_fields": []}} 请核实你的格式'
    elif interface == "/get_temp_info":
        if set(query_conds_keys) != {"省份", "城市", "日期"}:
            return f'/get_temp_info 接口格式为 {{"query_conds": {{"省份": "str", "城市": "str", "日期": "str"}}, "need_fields": []}} 请核实你的格式'
    elif len(query_conds_keys) != 1 or query_conds_keys[0] not in pos_key:
        tip = ""
        val = param["query_conds"][query_conds_keys[0]]
        if "事务所" in val:
            tip = "查询律师事务所接口为 /get_lawfirm_info"
        elif "法院" in val:
            tip = "查询法院代字，级别区划代码接口为 /get_court_code 查询法院联系方式地址负责人等接口为 /get_court_info"

        return f'{interface} 的参数 {param} 中的 "query_conds" 不符合要求，query_conds 下面的key应支持：{pos_key} 你应该确定你是接口使用错误还是参数传递错误 {tip}'

    error_need_fields = [field for field in need_fields if field not in api_info["可选need_fields字段"]]
    if error_need_fields:
        suggestion_back += f'{interface} 的参数 {param} 中的 need_fields 不符合要求，{error_need_fields} 不在可选字段 {api_info["可选need_fields字段"]} 内'
    return suggestion_back


sue_dic = {
    "/get_citizens_sue_citizens": [
        "原告",
        "原告性别",
        "原告生日",
        "原告民族",
        "原告工作单位",
        "原告地址",
        "原告联系方式",
        "原告委托诉讼代理人",
        "原告委托诉讼代理人联系方式",
        "被告",
        "被告性别",
        "被告生日",
        "被告民族",
        "被告工作单位",
        "被告地址",
        "被告联系方式",
        "被告委托诉讼代理人",
        "被告委托诉讼代理人联系方式",
        "诉讼请求",
        "事实和理由",
        "证据",
        "法院名称",
        "起诉日期",
    ],
    "/get_company_sue_citizens": [
        "原告",
        "原告地址",
        "原告法定代表人",
        "原告联系方式",
        "原告委托诉讼代理人",
        "原告委托诉讼代理人联系方式",
        "被告",
        "被告性别",
        "被告生日",
        "被告民族",
        "被告工作单位",
        "被告地址",
        "被告联系方式",
        "被告委托诉讼代理人",
        "被告委托诉讼代理人联系方式",
        "诉讼请求",
        "事实和理由",
        "证据",
        "法院名称",
        "起诉日期",
    ],
    "/get_citizens_sue_company": [
        "原告",
        "原告性别",
        "原告生日",
        "原告民族",
        "原告工作单位",
        "原告地址",
        "原告联系方式",
        "原告委托诉讼代理人",
        "原告委托诉讼代理人联系方式",
        "被告",
        "被告地址",
        "被告法定代表人",
        "被告联系方式",
        "被告委托诉讼代理人",
        "被告委托诉讼代理人联系方式",
        "诉讼请求",
        "事实和理由",
        "证据",
        "法院名称",
        "起诉日期",
    ],
    "/get_company_sue_company": [
        "原告",
        "原告地址",
        "原告法定代表人",
        "原告联系方式",
        "原告委托诉讼代理人",
        "原告委托诉讼代理人联系方式",
        "被告",
        "被告地址",
        "被告法定代表人",
        "被告联系方式",
        "被告委托诉讼代理人",
        "被告委托诉讼代理人联系方式",
        "诉讼请求",
        "事实和理由",
        "证据",
        "法院名称",
        "起诉日期",
    ],
}


def judge_param(route, param):
    if route in [
        "/get_citizens_sue_citizens",
        "/get_company_sue_citizens",
        "/get_citizens_sue_company",
        "/get_company_sue_company",
    ]:
        if not isinstance(param, dict):
            print(f"参数错误：参数为字典，key应该包括:{sue_dic[route]}")
            return
        else:
            duoyu = set(param.keys()) - set(sue_dic[route])
            shao = set(sue_dic[route]) - set(param.keys())
            s = ""
            if duoyu:
                s += f"多余或错误的key为：{duoyu}"
            if shao:
                s += f"缺少的key为：{shao}"
            if s:
                print(s)
                return
            else:
                return True
    if route in ["/get_sum", "/rank", "/save_dict_list_to_word"]:
        return True

    if route not in API_DICT:
        print("你的route没有被找到，请从API信息里找到正确的route并修改")
        return

    if not isinstance(param, dict) or {"query_conds", "need_fields"} - param.keys():
        print(
            "API info: param格式应该为",
            {"query_conds": {"key": "value"}, "need_fields": ["need_field1", "need_field2", ...]},
        )
        return

    api_info = API_DICT[route]
    suggestion_back = validate_params(route, param, api_info)
    if suggestion_back:
        print("API info:", suggestion_back)
        return

    # Special checks for company names
    for key in ["公司名称", "关联公司", "关联上市公司全称"]:
        if key in param["query_conds"] and len(param["query_conds"][key]) < 6:
            print(
                f'API info: 调用失败，你传入的公司名称可能是公司简称，通过/get_company_info 输入参数:{{"query_conds":{{"公司简称":你刚才的输入}},"need_fields":["公司名称"]}} 获取公司名称后继续'
            )
            return

    for key in ["公司名称", "关联公司", "公司代码", "案号", "法院名称", "律师事务所名称", "关联上市公司全称"]:
        if key in param["query_conds"]:
            text = param["query_conds"][key]
            pattern = r"(.)\1"
            if key == "案号":
                text1 = re.split("[\u4e00-\u9fa5]", text)[0]
                if re.findall(pattern, text1):
                    result = re.sub(pattern, r"\1", text)
                    print(
                        f"参数检测提示：你的参数{key}发现重复字符，修复后的结果为：{result}，如果调用正常请忽略此条提示，调用报错，优先使用本结果"
                    )
            elif key == "公司代码" and len(text) == 6:
                pass
            elif re.findall(pattern, text):
                result = re.sub(pattern, r"\1", text)
                print(
                    f"参数检测提示：你的参数{key}发现重复字符，修复后的结果为：{result}，如果调用正常请忽略此条提示，调用报错，优先使用本结果"
                )

    return True


def convert_date_format(date_str):
    if " " in date_str:
        date_str = date_str.split(" ")[0]
    # 尝试解析日期字符串
    try:
        # 处理 "2020-01-01" 格式
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # 若解析失败，尝试处理 "2020年01月1号" 格式
        try:
            date_obj = datetime.strptime(date_str, "%Y年%m月%d号")
        except ValueError:
            # 若解析失败，尝试处理 "2020年1月1号" 格式
            try:
                date_obj = datetime.strptime(date_str, "%Y年%m月%d号")
            except ValueError:
                # 若解析失败，尝试处理 "2020年1月1日" 格式
                try:
                    date_obj = datetime.strptime(date_str, "%Y年%m月%d日")
                except ValueError:
                    # 若解析失败，返回原字符串
                    return date_str

    # 格式化日期对象为所需格式
    formatted_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
    return formatted_date
