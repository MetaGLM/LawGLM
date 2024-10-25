"""
Author: lihaitao
Date: 2024-07-22 22:32:20
LastEditors: Do not edit
LastEditTime: 2024-08-04 17:00:48
FilePath: /GLM2024/GLM-0803sub/utils.py
"""

import json
from tool_register.tools import http_api_call


import re


def extract_court_code(text):
    # 案号的正则表达式
    case_number_pattern = re.compile(r"[(（](\d{4})[)）]([^\d]+?\d+)\D+\d+号")

    match = case_number_pattern.search(text)

    if match:
        court_code = match.group(2)
        return court_code
    else:
        return None


def remove_commas_from_numbers(text):
    number_with_commas_pattern = re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)")

    def replace_commas(match):
        return match.group(0).replace(",", "")

    cleaned_text = re.sub(number_with_commas_pattern, replace_commas, text)

    return cleaned_text


def get_court_name_by_subname(subname):
    if extract_court_code(subname) == None:  # 不是法院代字
        return ""
    api_name = "get_court_code"
    args = {"query_conds": {"法院代字": subname}, "need_fields": ["法院名称"]}
    ori_answer = http_api_call(api_name=api_name, data=args)
    if len(ori_answer["输出结果"]) != 0:
        return ori_answer["输出结果"][0]["法院名称"]
    return ""


def get_company_name_by_subname(subname):
    api_name = "get_company_info"
    args = {"query_conds": {"公司简称": subname}, "need_fields": ["公司名称"]}
    ori_answer = http_api_call(api_name=api_name, data=args)
    if len(ori_answer["输出结果"]) != 0:
        return ori_answer["输出结果"][0]["公司名称"]
    return ""


def get_true_address(subname):
    # 法院
    court_name = get_court_name_by_subname(subname)
    court_name = subname if court_name == "" else court_name
    if court_name != "" and len(court_name) >= 2 and court_name[-2:] == "法院":
        api_name = "get_court_info"
        args = {"query_conds": {"法院名称": court_name}, "need_fields": ["法院地址"]}
        ori_answer = http_api_call(api_name=api_name, data=args)
        if len(ori_answer["输出结果"]) != 0:
            return ori_answer["输出结果"][0]["法院地址"]

    if subname != "" and len(subname) >= 3 and subname[-3:] == "事务所":
        # 事务所
        api_name = "get_lawfirm_info"
        args = {"query_conds": {"律师事务所名称": subname}, "need_fields": ["律师事务所地址"]}
        ori_answer = http_api_call(api_name=api_name, data=args)
        if len(ori_answer["输出结果"]) != 0:
            return ori_answer["输出结果"][0]["律师事务所地址"]

    # 公司
    company_name = get_company_name_by_subname(subname)
    company_name = subname if company_name == "" else company_name
    if company_name != "" and len(company_name) >= 2 and company_name[-2:] == "公司":
        api_name = "get_company_register"
        args = {"query_conds": {"公司名称": company_name}, "need_fields": ["企业地址"]}
        ori_answer = http_api_call(api_name=api_name, data=args)
        if len(ori_answer["输出结果"]) != 0:
            return ori_answer["输出结果"][0]["企业地址"]

    return ""


def get_province_by_sub(sub_province):
    provices = [
        "北京市",
        "天津市",
        "上海市",
        "重庆市",
        "河北省",
        "山西省",
        "辽宁省",
        "吉林省",
        "黑龙江省",
        "江苏省",
        "浙江省",
        "安徽省",
        "福建省",
        "江西省",
        "山东省",
        "河南省",
        "湖北省",
        "湖南省",
        "广东省",
        "海南省",
        "四川省",
        "贵州省",
        "云南省",
        "陕西省",
        "甘肃省",
        "青海省",
        "台湾省",
        "内蒙古自治区",
        "广西壮族自治区",
        "西藏自治区",
        "宁夏回族自治区",
        "新疆维吾尔自治区",
        "香港特别行政区",
        "澳门特别行政区",
    ]
    for p in provices:
        if p.find(sub_province) != -1:
            return p
    return sub_province


def get_city_by_sub(sub_city):
    if sub_city != "" and sub_city[-1] == "市":
        return sub_city
    citys = [
        "北京市",
        "天津市",
        "上海市",
        "重庆市",
        "阿坝藏族羌族自治州",
        "阿克苏地区",
        "阿拉善盟",
        "阿勒泰地区",
        "阿里地区",
        "安康市",
        "安庆市",
        "安顺市",
        "安阳市",
        "鞍山市",
        "巴彦淖尔市",
        "巴音郭楞蒙古自治州",
        "巴中市",
        "白城市",
        "白山市",
        "白银市",
        "百色市",
        "蚌埠市",
        "包头市",
        "宝鸡市",
        "保定市",
        "保山市",
        "北海市",
        "本溪市",
        "毕节地区",
        "滨州市",
        "博尔塔拉蒙古自治州",
        "沧州市",
        "昌都地区",
        "昌吉回族自治州",
        "长春市",
        "长沙市",
        "长治市",
        "常德市",
        "常州市",
        "巢湖市",
        "朝阳市",
        "潮州市",
        "郴州市",
        "成都市",
        "承德市",
        "池州市",
        "赤峰市",
        "崇左市",
        "滁州市",
        "楚雄彝族自治州",
        "达州市",
        "大理白族自治州",
        "大连市",
        "大庆市",
        "大同市",
        "大兴安岭地区",
        "丹东市",
        "德宏傣族景颇族自治州",
        "德阳市",
        "德州市",
        "迪庆藏族自治州",
        "定西市",
        "东莞市",
        "东营市",
        "鄂尔多斯市",
        "鄂州市",
        "恩施土家族苗族自治州",
        "防城港市",
        "佛山市",
        "福州市",
        "抚顺市",
        "抚州市",
        "阜新市",
        "阜阳市",
        "甘南州",
        "甘孜藏族自治州",
        "赣州市",
        "固原市",
        "广安市",
        "广元市",
        "广州市",
        "贵港市",
        "贵阳市",
        "桂林市",
        "果洛藏族自治州",
        "哈尔滨市",
        "哈密地区",
        "海北藏族自治州",
        "海东地区",
        "海口市",
        "海南藏族自治州",
        "海西蒙古族藏族自治州",
        "邯郸市",
        "汉中市",
        "杭州市",
        "毫州市",
        "合肥市",
        "和田地区",
        "河池市",
        "河源市",
        "菏泽市",
        "贺州市",
        "鹤壁市",
        "鹤岗市",
        "黑河市",
        "衡水市",
        "衡阳市",
        "红河哈尼族彝族自治州",
        "呼和浩特市",
        "呼伦贝尔市",
        "湖州市",
        "葫芦岛市",
        "怀化市",
        "淮安市",
        "淮北市",
        "淮南市",
        "黄冈市",
        "黄南藏族自治州",
        "黄山市",
        "黄石市",
        "惠州市",
        "鸡西市",
        "吉安市",
        "吉林市",
        "济南市",
        "济宁市",
        "佳木斯市",
        "嘉兴市",
        "嘉峪关市",
        "江门市",
        "焦作市",
        "揭阳市",
        "金昌市",
        "金华市",
        "锦州市",
        "晋城市",
        "晋中市",
        "荆门市",
        "荆州市",
        "景德镇市",
        "九江市",
        "酒泉市",
        "喀什地区",
        "开封市",
        "克拉玛依市",
        "克孜勒苏柯尔克孜自治州",
        "昆明市",
        "拉萨市",
        "来宾市",
        "莱芜市",
        "兰州市",
        "廊坊市",
        "乐山市",
        "丽江市",
        "丽水市",
        "连云港市",
        "凉山彝族自治州",
        "辽阳市",
        "辽源市",
        "聊城市",
        "林芝地区",
        "临沧市",
        "临汾市",
        "临夏州",
        "临沂市",
        "柳州市",
        "六安市",
        "六盘水市",
        "龙岩市",
        "陇南市",
        "娄底市",
        "泸州市",
        "吕梁市",
        "洛阳市",
        "漯河市",
        "马鞍山市",
        "茂名市",
        "眉山市",
        "梅州市",
        "绵阳市",
        "牡丹江市",
        "内江市",
        "那曲地区",
        "南昌市",
        "南充市",
        "南京市",
        "南宁市",
        "南平市",
        "南通市",
        "南阳市",
        "宁波市",
        "宁德市",
        "怒江傈僳族自治州",
        "攀枝花市",
        "盘锦市",
        "平顶山市",
        "平凉市",
        "萍乡市",
        "莆田市",
        "濮阳市",
        "普洱市",
        "七台河市",
        "齐齐哈尔市",
        "黔东南苗族侗族自治州",
        "黔南布依族苗族自治州",
        "黔西南布依族苗族自治州",
        "钦州市",
        "秦皇岛市",
        "青岛市",
        "清远市",
        "庆阳市",
        "曲靖市",
        "衢州市",
        "泉州市",
        "日喀则地区",
        "日照市",
        "三门峡市",
        "三明市",
        "三亚市",
        "山南地区",
        "汕头市",
        "汕尾市",
        "商洛市",
        "商丘市",
        "上饶市",
        "韶关市",
        "邵阳市",
        "绍兴市",
        "深圳市",
        "沈阳市",
        "十堰市",
        "石家庄市",
        "石嘴山市",
        "双鸭山市",
        "朔州市",
        "四平市",
        "松原市",
        "苏州市",
        "宿迁市",
        "宿州市",
        "绥化市",
        "随州市",
        "遂宁市",
        "塔城地区",
        "台州市",
        "太原市",
        "泰安市",
        "泰州市",
        "唐山市",
        "天水市",
        "铁岭市",
        "通化市",
        "通辽市",
        "铜川市",
        "铜陵市",
        "铜仁市",
        "吐鲁番地区",
        "威海市",
        "潍坊市",
        "渭南市",
        "温州市",
        "文山壮族苗族自治州",
        "乌海市",
        "乌兰察布市",
        "乌鲁木齐市",
        "无锡市",
        "吴忠市",
        "芜湖市",
        "梧州市",
        "武汉市",
        "武威市",
        "西安市",
        "西宁市",
        "西双版纳傣族自治州",
        "锡林郭勒盟",
        "厦门市",
        "咸宁市",
        "咸阳市",
        "湘潭市",
        "湘西土家族苗族自治州",
        "襄樊市",
        "孝感市",
        "忻州市",
        "新乡市",
        "新余市",
        "信阳市",
        "兴安盟",
        "邢台市",
        "徐州市",
        "许昌市",
        "宣城市",
        "雅安市",
        "烟台市",
        "延安市",
        "延边朝鲜族自治州",
        "盐城市",
        "扬州市",
        "阳江市",
        "阳泉市",
        "伊春市",
        "伊犁哈萨克自治州",
        "宜宾市",
        "宜昌市",
        "宜春市",
        "益阳市",
        "银川市",
        "鹰潭市",
        "营口市",
        "永州市",
        "榆林市",
        "玉林市",
        "玉树藏族自治州",
        "玉溪市",
        "岳阳市",
        "云浮市",
        "运城市",
        "枣庄市",
        "湛江市",
        "张家界市",
        "张家口市",
        "张掖市",
        "漳州市",
        "昭通市",
        "肇庆市",
        "镇江市",
        "郑州市",
        "中山市",
        "中卫市",
        "舟山市",
        "周口市",
        "株洲市",
        "珠海市",
        "驻马店市",
        "资阳市",
        "淄博市",
        "自贡市",
        "遵义市",
    ]
    for c in citys:
        if c.find(sub_city) != -1:
            return c
    return sub_city


import re

import re

# 示例日期字符串列表
date_strings = ["2019-8-1", "2019-08-01", "2019-8-01", "2019-08-1"]

# 正则表达式模式
pattern1 = r"(\d{4})-(\d{1,2})-(\d{1,2})"
pattern2 = r"(\d{4})年(\d{1,2})月(\d{1,2})日"


# 转换函数
# mode = 1, 输出2019年08月01日
# mode = 2, 输出2019年8月1日
def convert_date_format(date_string, output_mode):
    matches = re.finditer(pattern1, date_string)
    for match in matches:
        year, month, day = match.groups()
        date_string = date_string.replace(
            match.group(0),
            f"{year}年{int(month):02d}月{int(day):02d}日"
            if output_mode == 1
            else f"{year}年{int(month)}月{int(day)}日",
        )
    matches = re.finditer(pattern2, date_string)
    for match in matches:
        year, month, day = match.groups()
        date_string = date_string.replace(
            match.group(0),
            f"{year}年{int(month):02d}月{int(day):02d}日"
            if output_mode == 1
            else f"{year}年{int(month)}月{int(day)}日",
        )
    return date_string


def correct_args(api_name, api_args):
    other_observation = ""
    try:
        if isinstance(api_args["need_fields"], dict):
            api_args["need_fields"] = list(api_args["need_fields"].values())[0]
        if isinstance(api_args["need_fields"], list) == False or api_args["need_fields"][0] == "*":
            api_args["need_fields"] = []
    except:
        api_args["need_fields"] = []

    try:
        if "上市公司投资金额" in api_args["need_fields"] and "上市公司参股比例" not in api_args["need_fields"]:
            api_args["need_fields"].append("上市公司参股比例")

        temp = []
        # 将api_args['need_fields']所有 '级别' 替换为 ["法院级别", "行政级别", "级别"]，其他保留
        for arg in api_args["need_fields"]:
            if arg.find("级别") != -1:
                for i in ["法院级别", "行政级别", "级别"]:
                    if i not in temp:
                        temp.append(i)
            else:
                temp.append(arg)
        api_args["need_fields"] = temp

        temp = api_args["need_fields"]
        # 若api_args['need_fields']中有 '律师事务所', 则添加 ['原告', '被告']，其他保留
        if (
            "原告律师事务所" in api_args["need_fields"]
            or "被告律师事务所" in api_args["need_fields"]
            or "原告" in api_args["need_fields"]
            or "被告" in api_args["need_fields"]
        ):
            api_args["need_fields"].append("原告")
            api_args["need_fields"].append("原告律师事务所")
            api_args["need_fields"].append("被告")
            api_args["need_fields"].append("被告律师事务所")
            api_args["need_fields"] = list(set(api_args["need_fields"]))
        # for arg in api_args['need_fields']:
        #     if arg.find('原告律师事务所') != -1 or arg.find('被告律师事务所') != -1:
        #         for i in ["原告", "被告"]:
        #             if i not in temp:
        #                 temp.append(i)
        # api_args['need_fields'] = temp

        if api_name != "get_address_code":
            if "日期" in api_args["query_conds"].keys():
                api_args["need_fields"].append("日期")
            if "案由" in api_args["query_conds"].keys():
                api_args["need_fields"].append("案由")
            if "文书类型" in api_args["query_conds"].keys():
                api_args["need_fields"].append("文书类型")

        if api_name == "get_legal_document_list":
            if "原告" in api_args["query_conds"].keys():
                api_args["need_fields"].append("原告")
                api_args["need_fields"].append("原告律师事务所")
                api_args["need_fields"].append("被告")
                api_args["need_fields"].append("被告律师事务所")
                api_args["need_fields"] = list(set(api_args["need_fields"]))
                if "关联公司" not in api_args["query_conds"].keys():
                    api_args["query_conds"] = {"关联公司": api_args["query_conds"]["原告"]}
            if "被告" in api_args["query_conds"].keys():
                api_args["need_fields"].append("被告")
                api_args["need_fields"].append("被告律师事务所")
                api_args["need_fields"].append("原告")
                api_args["need_fields"].append("原告律师事务所")
                api_args["need_fields"] = list(set(api_args["need_fields"]))
                if "关联公司" not in api_args["query_conds"].keys():
                    api_args["query_conds"] = {"关联公司": api_args["query_conds"]["被告"]}

        if api_name == "get_legal_document_list":  # 添加案号，方便后续筛选
            api_args["need_fields"].append("案号")
            api_args["need_fields"] = list(set(api_args["need_fields"]))

        if (
            api_name == "get_legal_document"
            and ("案号" in api_args["query_conds"].keys())
            and ("法院名称" in api_args["need_fields"] or "审理法院" in api_args["need_fields"])
        ):
            # 特殊情况：试图通过案号直接搜索法院名称
            court_code = extract_court_code(api_args["query_conds"]["案号"])
            api_name = "get_court_code"
            api_args["query_conds"] = {"法院代字": court_code}
            api_args["need_fileds"] = ["法院名称"]

        if "法院代字" in api_args["query_conds"].keys() and api_name != "get_court_code":
            full_name = get_court_name_by_subname(api_args["query_conds"]["法院代字"])  # 直接尝试获取法院名称
            if full_name != "":
                api_args["query_conds"] = {"法院名称": full_name}
                other_observation += f"法院名称是{full_name}\n"

        if "法院名称" in api_args["query_conds"].keys() and "关联公司" not in api_args["query_conds"].keys():
            full_name = get_court_name_by_subname(api_args["query_conds"]["法院名称"])  # 直接尝试获取法院名称
            if full_name != "":
                api_args["query_conds"]["法院名称"] = full_name
                other_observation += f"法院名称是{full_name}\n"
            api_args["query_conds"] = {"法院名称": api_args["query_conds"]["法院名称"]}

        if "地址" in api_args["query_conds"].keys() and api_name == "get_address_info":
            true_address = get_true_address(api_args["query_conds"]["地址"])
            if true_address != "":
                api_args["query_conds"]["地址"] = true_address
                other_observation += f"地址是{true_address}\n"
            api_args["query_conds"] = {"地址": api_args["query_conds"]["地址"]}

        if "公司名称" in api_args["query_conds"].keys():
            full_name = get_company_name_by_subname(api_args["query_conds"]["公司名称"])  # 直接尝试获取公司名称
            if full_name != "":
                api_args["query_conds"]["公司名称"] = full_name
                other_observation += f"公司名称是{full_name}\n"
            api_args["query_conds"] = {"公司名称": api_args["query_conds"]["公司名称"]}

        if "统一社会信用代码" in api_args["query_conds"].keys():
            api_args["query_conds"] = {"统一社会信用代码": api_args["query_conds"]["统一社会信用代码"]}

        if "关联上市公司全称" in api_args["query_conds"].keys():
            full_name = get_company_name_by_subname(
                api_args["query_conds"]["关联上市公司全称"]
            )  # 直接尝试获取公司名称
            if full_name != "":
                api_args["query_conds"]["关联上市公司全称"] = full_name
                other_observation += f"公司名称是{full_name}\n"
            api_args["query_conds"] = {"关联上市公司全称": api_args["query_conds"]["关联上市公司全称"]}

        if "案号" in api_args["query_conds"].keys() and "关联公司" not in api_args["query_conds"].keys():
            api_args["query_conds"] = {"案号": api_args["query_conds"]["案号"]}

        if "关联公司" in api_args["query_conds"].keys():
            full_name = get_company_name_by_subname(api_args["query_conds"]["关联公司"])  # 直接尝试获取公司名称
            if full_name != "":
                api_args["query_conds"]["关联公司"] = full_name
                other_observation += f"公司名称是{full_name}\n"
            api_args["query_conds"] = {"关联公司": api_args["query_conds"]["关联公司"]}

        if "律师事务所名称" in api_args["query_conds"].keys():
            api_args["query_conds"] = {"律师事务所名称": api_args["query_conds"]["律师事务所名称"]}

        # 参数出现 省份、城市、区县的情况： 1.[省份、城市、日期]  2.[省份、城市、区县]

        # 省份在，则城市一定在，如果省份在，城市不在，则试图根据直辖市填充
        if "省份" in api_args["query_conds"].keys() and "城市" not in api_args["query_conds"].keys():
            if api_args["query_conds"]["省份"] in ["北京市", "天津市", "上海市", "重庆市"]:
                api_args["query_conds"]["城市"] = api_args["query_conds"]["省份"]

        # 城市在，则省份一定在，如果城市在，省份不在，则试图根据直辖市填充
        if "城市" in api_args["query_conds"].keys() and "省份" not in api_args["query_conds"].keys():
            if api_args["query_conds"]["城市"] in ["北京市", "天津市", "上海市", "重庆市"]:
                api_args["query_conds"]["省份"] = api_args["query_conds"]["城市"]

        # 区县在，则省份、城市一定都在，如果省份、城市都不在，参数错误
        if "区县" in api_args["query_conds"].keys() and api_name == "get_address_code":
            if (
                "省份" in api_args["query_conds"].keys() and "城市" in api_args["query_conds"].keys()
            ):  # 矫正省份、城市格式
                api_args["query_conds"]["省份"] = get_province_by_sub(api_args["query_conds"]["省份"])
                api_args["query_conds"]["城市"] = get_city_by_sub(api_args["query_conds"]["城市"])
                api_args["query_conds"] = {
                    "省份": api_args["query_conds"]["省份"],
                    "城市": api_args["query_conds"]["城市"],
                    "区县": api_args["query_conds"]["区县"],
                }
        # 日期在，则省份、城市、区县一定都在
        if "日期" in api_args["query_conds"].keys() and api_name == "get_temp_info":
            if (
                "省份" in api_args["query_conds"].keys() and "城市" in api_args["query_conds"].keys()
            ):  # 矫正省份、城市格式
                api_args["query_conds"]["省份"] = get_province_by_sub(api_args["query_conds"]["省份"])
                api_args["query_conds"]["城市"] = get_city_by_sub(api_args["query_conds"]["城市"])
                api_args["query_conds"] = {
                    "省份": api_args["query_conds"]["省份"],
                    "城市": api_args["query_conds"]["城市"],
                    "日期": convert_date_format(api_args["query_conds"]["日期"], 2),
                }

        api_args["need_fields"] = list(set(api_args["need_fields"]))
    except:
        pass

    return api_name, api_args, other_observation


import concurrent.futures
from tqdm import tqdm


def multi_thread_excute(all_tasks, parralle_num=20):
    """
    多线程运行任务，注意，返回结果序并不和all_tasks一致，请设计好task的输出，能够通过map的形式找到对应的答案
    """

    def multi_thread_excute_helper(tasks):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            exe_tasks = [executor.submit(*task) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(exe_tasks)]
        return results

    all_results = []
    for i in tqdm(range(0, len(all_tasks), parralle_num)):
        all_results += multi_thread_excute_helper(all_tasks[i : i + parralle_num])
    return all_results
