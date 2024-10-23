import json, re
import requests

from copy import deepcopy
from zhipuai import ZhipuAI

from new_logtool import VLOG

API_KEY = ""
TEAM_TOKEN = ""

NAME_MAP = {
    "company_name": "公司名称",
    "court_name": "法院名称",
    "court_code": "法院代字",
    "company_social_id": "统一社会信用代码",
    "case_id": "案号",
    "lawfirm_name": "律师事务所名称",
    "address": "地址",
    "province": "省份",
    "city": "城市",
    "county": "区县",
    "date": "日期",
    "公司名称": "公司名称",
    "公司简称": "公司简称",
    "公司代码": "公司代码",
    "法院名称": "法院名称",
    "统一社会信用代码": "统一社会信用代码",
    "案号": "案号",
    "律师事务所名称": "律师事务所名称",
    "地址": "地址",
    "省份": "省份",
    "城市": "城市",
    "区县": "区县",
    "日期": "日期",
}

ALL_TOOLS = [
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "根据公司名称、公司简称或公司代码（只有6位数字）查找上市公司信息。参数为中文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "查询key的名称：限制为[公司名称, 公司简称, 公司代码]任意一个。",
                    },
                    "value": {
                        "type": "string",
                        "description": "对应的具体的公司名称/公司简称/公司代码。",
                    },
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_company_register",
            "description": "根据公司名称，获得该公司的注册信息。参数为中文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "api_type": "API2",
        "type": "function",
        "function": {
            "name": "get_company_register_name",
            "description": "根据统一社会信用代码查询公司名称。统一社会信用代码格式为18个数字和字母组成的字符，例如：91610000745016111K。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_social_id": {
                        "type": "string",
                        "description": "统一社会信用代码",
                    }
                },
                "required": ["company_social_id"],
            },
        },
    },
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_sub_company_info",
            "description": "通过子公司来查母公司：根据公司名称，获得该公司的关联公司信息。参数为中文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_sub_company_info_list",
            "description": "通过母公司来查子公司：参数为中文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "api_type": "API3",
        "type": "function",
        "function": {
            "name": "get_legal_document",
            "description": "通过案号查询裁判文书相关信息：包括原告和被告，原告律师和被告律师，判决结果和审理依据等。案号的格式为：(2019)川0103民初3382号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "案号",
                    }
                },
                "required": ["case_id"],
            },
        },
    },
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_legal_document_list",
            "description": "通过公司名称查询该公司涉及的案件列表（法律文书信息）",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "api_type": "API4",
        "type": "function",
        "function": {
            "name": "get_court_info",
            "description": "根据法院名称查询法院基础信息，包括负责人、地址、联系方式等",
            "parameters": {
                "type": "object",
                "properties": {
                    "court_name": {
                        "type": "string",
                        "description": "法院名称",
                    }
                },
                "required": ["court_name"],
            },
        },
    },
    {
        "api_type": "API4",
        "type": "function",
        "function": {
            "name": "get_court_code",
            "description": "根据法院名称查询法院代字",
            "parameters": {
                "type": "object",
                "properties": {
                    "court_name": {
                        "type": "string",
                        "description": "法院名称",
                    }
                },
                "required": ["court_name"],
            },
        },
    },
    {
        "api_type": "API5",
        "type": "function",
        "function": {
            "name": "get_lawfirm_info",
            "description": "根据律师事务所名称查询该所基础信息，包括负责人、注册资本、地址、联系方式等",
            "parameters": {
                "type": "object",
                "properties": {
                    "lawfirm_name": {
                        "type": "string",
                        "description": "律师事务所名称",
                    }
                },
                "required": ["lawfirm_name"],
            },
        },
    },
    {
        "api_type": "API5",
        "type": "function",
        "function": {
            "name": "get_lawfirm_log",
            "description": "根据律师事务所名称查询该所统计数据，包括服务过的公司信息等",
            "parameters": {
                "type": "object",
                "properties": {
                    "lawfirm_name": {
                        "type": "string",
                        "description": "律师事务所名称",
                    }
                },
                "required": ["lawfirm_name"],
            },
        },
    },
    {
        "api_type": "API6_1",
        "type": "function",
        "function": {
            "name": "get_address_info",
            "description": "根据详细的地址查该地址对应的省份城市区县，例子：保定市天威西路2222号",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "地址",
                    }
                },
                "required": ["address"],
            },
        },
    },
    {
        "api_type": "API6_2",
        "type": "function",
        "function": {
            "name": "get_address_code",
            "description": "根据地址：省份城市区县查对应的区划代码，例子：江苏省 连云港市 连云港高新技术产业开发区，需要包含'省'、'市'、'区'、'县'等行政单位",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "省份",
                    },
                    "city": {
                        "type": "string",
                        "description": "城市",
                    },
                    "county": {
                        "type": "string",
                        "description": "区县",
                    },
                },
                "required": ["province", "city", "county"],
            },
        },
    },
    {
        "api_type": "API6_3",
        "type": "function",
        "function": {
            "name": "get_temp_info",
            "description": "根据日期及省份城市查询天气相关信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "省份",
                    },
                    "city": {
                        "type": "string",
                        "description": "城市",
                    },
                    "date": {
                        "type": "string",
                        "description": "日期",
                    },
                },
                "required": ["province", "city", "date"],
            },
        },
    },
    {
        "api_type": "API3",
        "type": "function",
        "function": {
            "name": "get_legal_abstract",
            "description": "根据案号查法律文书摘要",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "案号",
                    }
                },
                "required": ["case_id"],
            },
        },
    },
    {
        "api_type": "API1",
        "type": "function",
        "function": {
            "name": "get_xzgxf_info_list",
            "description": "根据公司名称查询所有限制高消费相关信息list",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称",
                    }
                },
                "required": ["company_name"],
            },
        },
    },
]

PROVINCE = [
    "皖",
    "京",
    "渝",
    "闽",
    "甘",
    "粤",
    "桂",
    "贵",
    "琼",
    "冀",
    "豫",
    "黑",
    "鄂",
    "湘",
    "吉",
    "苏",
    "赣",
    "辽",
    "内",
    "宁",
    "青",
    "鲁",
    "晋",
    "陕",
    "沪",
    "川",
    "津",
    "藏",
    "新",
    "港",
    "云",
    "澳",
    "浙",
    "宁",
    "兵",
    "军",
    "最高法",
]

PROVINCE_LIST = "|".join(PROVINCE)

PROVINCE_NAME = [
    "安徽",
    "福建",
    "甘肃",
    "广东",
    "广西",
    "贵州",
    "海南",
    "河北",
    "河南",
    "黑龙江",
    "湖北",
    "湖南",
    "吉林" "江苏",
    "江西",
    "辽宁",
    "青海",
    "山东",
    "山西",
    "陕西",
    "四川",
    "云南",
    "浙江",
]

CITY_LIST = ["北京", "上海", "天津", "重庆"]
CITY_LIST_STR = "|".join(CITY_LIST)


class TOOLS:
    def api(api_name, args):
        is_API18 = False
        API18_caseid = ""
        API18_courtcode = ""
        if api_name == "get_court_name":
            is_API18 = True
            api_name = "get_court_code"
            API18_caseid = args["case_id"]
            API18_courtcode = TOOLS.transfer_courtcode(args["case_id"])
            args = {"court_code": API18_courtcode}

        url = f"https://comm.chatglm.cn/law_api/s1_b/{api_name}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TEAM_TOKEN}"}

        VLOG[2](api_name, args)

        querty_conds = {}

        for key, value in args.items():
            if api_name == "get_sub_company_info_list" and key == "company_name":
                querty_conds["关联上市公司全称"] = value
            elif api_name == "get_xzgxf_info_list" and key == "company_name":
                querty_conds["限制高消费企业名称"] = value
            elif api_name == "get_legal_document_list" and key == "company_name":
                querty_conds["关联公司"] = value
            elif key in NAME_MAP:
                querty_conds[NAME_MAP[key]] = value
            elif "key" in args and "value" in args:
                querty_conds[args["key"]] = args["value"]
            else:
                VLOG[2]("error key:", key, value)

        if api_name == "get_temp_info":
            if querty_conds["省份"] in ("北京市", "天津市", "重庆市", "上海市"):
                querty_conds["城市"] = querty_conds["省份"]
            querty_conds["日期"] = TOOLS.transfer_date(querty_conds["日期"])
            VLOG[2]("GET_TEMP_INFO:", querty_conds)

        data = {"query_conds": querty_conds, "need_fields": []}
        rsp = requests.post(url, data=json.dumps(data), headers=headers).json()

        if is_API18:
            try:
                rsp["案号"] = API18_caseid
                rsp["法院代字"] = API18_courtcode
            except:
                pass

        VLOG[2]("API Response:", api_name, args, "|", rsp)
        return rsp

    def sue_api(api_name, args):
        url = f"https://comm.chatglm.cn/law_api/s1_b/{api_name}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TEAM_TOKEN}"}

        VLOG[2](api_name, args)

        rsp = requests.post(url, data=json.dumps(args), headers=headers)
        VLOG[2]("API Response:", api_name, args, "|", rsp.json())
        return rsp.json()

    def get_api_tools(api_list):
        tools = []
        for api in set(api_list):
            for tool in deepcopy(ALL_TOOLS):
                if tool["api_type"] == api:
                    tool.pop("api_type")
                    tools.append(tool)
        return tools

    def get_tools_response(query, tools):
        messages = [{"role": "user", "content": query}]

        client = ZhipuAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="glm-4",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        if not response.choices[0].message.tool_calls:
            return None, None
        function = response.choices[0].message.tool_calls[0].function
        func_args = function.arguments
        func_name = function.name
        VLOG[2]("GET_TOOL:", function, func_name, func_args)
        return func_name, json.loads(func_args)

    # 解析LLM生成的json
    def prase_json_from_response(rsp: str):
        pattern = r"```json(.*?)```"
        rsp_json = None
        try:
            match = re.search(pattern, rsp, re.DOTALL)
            if match is not None:
                try:
                    rsp_json = json.loads(match.group(1).strip())
                except:
                    pass
            else:
                rsp_json = json.loads(rsp)
            return rsp_json
        except json.JSONDecodeError as e:
            raise ("Json Decode Error: {error}".format(error=e))

    @staticmethod
    def caseid_augment(case_id):
        pattern = r"\({0,1}\d{4}\){0,1}[\u4e00-\u9fa5]{1}\d{1,5}[\u4e00-\u9fa5]{1,3}\d{1,6}号"
        result = re.findall(pattern, case_id)
        if result:
            for xres in result:
                xpattern = r"[\u4e00-\u9fa5]{1}\d{1,5}"
                court_code = re.search(xpattern, xres).group()
                case_id = case_id.replace(xres, xres + f"(法院代字:{court_code})")
        return case_id

    @staticmethod
    def caseid_search(question):
        pattern = r"\({0,1}\d{4}\){0,1}[\u4e00-\u9fa5]{1}\d{0,5}[\u4e00-\u9fa5]{1,3}\d{1,6}号"
        result = re.findall(pattern, question)
        return result

    @staticmethod
    def caseid_search2(question):
        pattern1 = r"\({0,1}\d{4}\){0,1}[\u4e00-\u9fa5]{1}\d{0,5}[\u4e00-\u9fa5]{1,3}\d{1,6}号"
        result = re.findall(pattern1, question)
        pattern2 = r"\（{0,1}\d{4}\）{0,1}[\u4e00-\u9fa5]{1}\d{0,5}[\u4e00-\u9fa5]{1,3}\d{1,6}号"
        result2 = re.findall(pattern2, question)
        return result + result2

    @staticmethod
    def wrapper_list_text(data):
        if isinstance(data, list):
            return data
        else:
            data = (
                data.strip()
                .replace("，", ",")
                .replace("、", ",")
                .replace("和", ",")
                .replace(";", ",")
                .replace("；", ",")
                .split(",")
            )
            data = [x.strip() for x in data if x.strip()]
            return data

    @staticmethod
    def wrapper_list(data):
        return data if isinstance(data, list) else [data]

    @staticmethod
    def transfer_date(date):
        if "年" not in date:
            if date.count("-") == 2:
                date = date.replace("-", "年", 1).replace("-", "月") + "日"
            elif date.count("-") == 1:
                date = date.replace("-", "年") + "月"
            else:
                date = date[0:4] + "年" + date[4:6] + "月" + int(date[6:8]) + "日"

        date = (
            date.split("年", 1)[0]
            + "年"
            + str(int(date.split("年", 1)[1].split("月", 1)[0]))
            + "月"
            + str(int(date.split("月", 1)[1].split("日", 1)[0]))
            + "日"
        )
        return date

    @staticmethod
    def transfer_courtcode(caseid):
        if not caseid:
            return caseid
        pattern = r"(%s){1}\d{1,5}" % (PROVINCE_LIST)
        res = re.search(pattern, caseid)
        if res:
            return res.group()
        else:
            pattern2 = r"(%s){1}" % (PROVINCE_LIST)
            res2 = re.search(pattern2, caseid)
            if res2:
                return res2.group()

            VLOG[2]("WARNNING_COURT_CODE:", caseid)
            return caseid

    @staticmethod
    def transfer_cash(cash):
        if cash == "-":
            return 0
        cash = cash.replace("元", "").replace(",", "")
        amount = 0
        try:
            amount = float(cash)
        except Exception as e:
            VLOG[2]("ERROR_TRANSFER_CASE:", e)
            if "万" in cash:
                amount = float(cash.replace("万", "")) * 10000
            if "亿" in cash:
                amount = float(cash.replace("亿", "")) * 100000000
        return amount

    @staticmethod
    def transfor_rate(rate):
        if not rate:
            return 0
        pattern = r"\d+\.?\d*"
        res = re.search(pattern, rate)
        if res:
            return int(float(res.group()))
        else:
            return 0

    @staticmethod
    def api_sue(api_name, args):
        url = f"https://comm.chatglm.cn/law_api/s1_b/{api_name}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TEAM_TOKEN}"}

        VLOG[2](api_name, args)

        querty_conds = {}

        data = {"query_conds": querty_conds, "need_fields": []}
        rsp = requests.post(url, data=json.dumps(data), headers=headers)
        VLOG[2]("API Response:", api_name, args, "|", rsp.json())
        return rsp.json()

    @staticmethod
    def fix_address(address={}):
        if "city" in address:
            for city in CITY_LIST:
                if city in address["city"]:
                    address["city"] = city + "市"
                    address["province"] = city + "市"
                    break
            if "市" not in address["city"]:
                address["city"] = address["city"] + "市"
        if "province" in address:
            if "区" not in address["province"] and "市" not in address["province"] and "省" not in address["province"]:
                address["province"] = address["province"] + "省"
        return address

    @staticmethod
    def fix_court_name(court_name):
        for city in CITY_LIST:
            if city in court_name and city + "市" not in court_name:
                court_name = court_name.replace(city, city + "市")
                break
        for province in PROVINCE_NAME:
            if province in court_name and province + "省" not in court_name:
                court_name = court_name.replace(province, province + "省")
                break
        if "中级" in court_name and "市" not in court_name and "自治州" not in court_name:
            court_name = court_name.replace("中级", "市中级")
        return court_name
