from api import call_api
from copy import deepcopy
import re
import contextlib
import io
import jieba.analyse


# 法院|get_court_code_by_case_number
# 根据`案号`匹配法院代字，然后查询`CourtCode`表格，可以["法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"]获取性能稳定
def get_court_code_by_case_number(param):
    """
    根据案号查询法院信息："法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"，不可以获取法院地点，
    其中案号格式为：(+收案年度+)+法院代字+类型代字+案件编号+号
    :param param: {'query_conds': {'案号': 'str'}, "need_fields": ["法院名称", "行政级别", "法院级别", "法院代字", "区划代码","级别"]}
    :return:
    """
    dic = {"法院名称": "", "行政级别": "", "法院级别": "", "法院代字": "", "区划代码": "", "级别": ""}
    try:
        case_number = param["query_conds"]["案号"]
        match1 = re.search(r"[(（](?P<year>\d+)[)）](?P<area_code>\D)", case_number)
        if match1:
            area_code = match1.group("area_code")
            match2 = re.search(rf"{re.escape(area_code)}(?P<court_code>\d*)", case_number)
            if match2:
                court_code = match2.group("court_code")
            else:
                court_code = ""
            info1 = call_api(
                "/get_court_code",
                {"query_conds": {"法院代字": area_code + court_code}, "need_fields": []},
                print_str=False,
            )
            if info1:
                print("与此案号相关的法院信息查询结果为:", info1)
                return info1
            else:
                return dic
        else:
            print("Traceback:案号不标准")
            return dic
    except:
        print(
            'Traceback:错误参数或者是案号错误 需要的参数格式为：{"query_conds": {"案号": str}, "need_fields": []}，你的参数为：',
            param,
            "请确保参数正确或合理猜测案号",
        )
        try:
            dic["法院代字"] = area_code + court_code
            return dic
        except:
            return dic


# /get_legal_document_list|filter_legal_docs
# 过滤法律文档信息，从法律文档列表中过滤出符合条件的文档，支持legal_documents表中的字段，如原告被告律师事务所等，但是不支持胜诉方等
def filter_legal_docs(legal_documents_result, filter_dict):
    """
    过滤法律文档信息
    根据指定的过滤条件，从法律文档列表中过滤出符合条件的文档。案号格式为：(+收案年度+)+法院代字+类型代字+案件编号+号。
    参数:
    legal_documents_result (list[dict]): 通过 get_legal_document_list 接口获得的法律文档列表。
    param filter_dict (dict): 包含过滤条件的字典
        - 案由 (str): 案件的案由，支持模糊匹配，但是必须是关键词例如:劳务纠纷,债权纠纷，侵害商标权纠纷。
        - 年份 (str): 案件的年份，例如 '2019'。
        - 年份类型 (str): 年份的类型，可以是 '立案日期'、'起诉日期' 或 '审理日期'。
        - 审理省份: (str) 案件审理的省份，注意是简称，例如 安徽省->皖 四川->川
        - 案件类型 (str): 案件类型，可以是 ['民', '民初', '民终', '执','民申'] 之一。
            - '民': 民事诉讼
            - '民初': 民事诉讼初审
            - '民终': 民事诉讼终审
            - '执': 执行案件
        - 原告 (str): 案件的原告。
        - 被告 (str): 案件的被告。
        - 最小涉案金额 (str): 案件的最小涉案金额，支持 1亿，10万这种描述,涉案金额不为0的填“0”
        - 最大涉案金额 (str): 案件的最大涉案金额，支持 1亿，10万这种描述
        - 法院代字(str): 审理法院的代字
    注意：字段只有在需要的时候才存在，例如筛选2019年的执行案件只需要{'年份':'2019','年份类型':'立案日期','案件类型':'执'}。
    返回:
        list[dict]: 包含符合条件的法律文档信息的列表。
    """
    if not set(filter_dict.keys()) < {
        "案由",
        "年份",
        "年份类型",
        "案件类型",
        "原告",
        "被告",
        "最小涉案金额",
        "最大涉案金额",
        "审理省份",
    }:
        print(
            "Traceback:请仔细阅读文档，你的过滤条件不支持,你可以过滤的条件key为:'案由','年份','年份类型','案件类型','原告','被告','最小涉案金额','最大涉案金额','审理省份' 请阅读文档后重新调用或自己实现筛选"
        )
        return []
    try:
        if isinstance(legal_documents_result, dict):
            legal_documents_result = [legal_documents_result]
        if "案件类型" in filter_dict and filter_dict["案件类型"]:
            legal_documents_result = [i for i in legal_documents_result if filter_dict["案件类型"] in i["案号"]]
        if "原告" in filter_dict and filter_dict["原告"]:
            legal_documents_result = [i for i in legal_documents_result if filter_dict["原告"] in i["原告"]]
        if "被告" in filter_dict and filter_dict["被告"]:
            legal_documents_result = [i for i in legal_documents_result if filter_dict["被告"] in i["被告"]]
        if "审理省份" in filter_dict and filter_dict["审理省份"]:
            legal_documents_result = [i for i in legal_documents_result if filter_dict["审理省份"] in i["案号"]]
        if "案由" in filter_dict and filter_dict["案由"]:
            keywords_tfidf = jieba.analyse.extract_tags(filter_dict["案由"], topK=5, withWeight=False)
            legal_documents_result_reasons = []
            for i in legal_documents_result:
                if keywords_tfidf[0] in i["案由"]:
                    legal_documents_result_reasons.append(i)
        else:
            legal_documents_result_reasons = legal_documents_result
        if "年份" in filter_dict and filter_dict["年份"]:
            filter_legal_documents_result = []
            for i in legal_documents_result_reasons:
                if "年份类型" in filter_dict and filter_dict["年份类型"] in ["审理日期"]:
                    if i["日期"].startswith(filter_dict["年份"]):
                        filter_legal_documents_result.append(i)
                else:
                    if f"({filter_dict['年份']})" in i["案号"] or f"（{filter_dict['年份']}）" in i["案号"]:
                        filter_legal_documents_result.append(i)
        else:
            filter_legal_documents_result = legal_documents_result_reasons
        if "最小涉案金额" in filter_dict:
            min_case = map_str_to_num(filter_dict.get("最小涉案金额"))
            filter_legal_documents_result = [
                i for i in filter_legal_documents_result if map_str_to_num(i["涉案金额"]) > min_case
            ]
        if "最大涉案金额" in filter_dict:
            max_case = map_str_to_num(filter_dict.get("最大涉案金额"))
            filter_legal_documents_result = [
                i for i in filter_legal_documents_result if map_str_to_num(i["涉案金额"]) < max_case
            ]
        if "法院代字" in filter_dict:
            fy_code = filter_dict["法院代字"]
            filter_legal_documents_result = [
                i for i in filter_legal_documents_result if re.search(fy_code + "(?!\d)", i["案号"])
            ]
        print(f"过滤后的结果为:{filter_legal_documents_result}")
        return filter_legal_documents_result
    except KeyError as e:
        print(f"""Traceback:你在之前没有获取{e}这个字段，请先获取此字段再来过滤""")
        return []
    except Exception as e:
        print(f"""
Traceback:
{e}
你的参数错误或者是之前的步骤有问题，请按照以下方式排查：
需要的参数为：
legal_documents_result: 通过 get_legal_document_list 接口获得的数据，需要在need_fields加入相关字段，如：案由，日期，案号，原告，被告等
filter_dict:你的过滤条件，是一个字典，如下所示：{{"案由":"str",'年份':'2019','年份类型':'立案日期/起诉日期/审理日期','原告':'xxx','被告':'xxx'}}" 可以省略不必要的字段，或者将不必要的字段填空。
你当前的参数为：
legal_documents_result:{legal_documents_result[:3]} # 只显示前三条
filter_dict:{filter_dict}
请分析原因，如果是 legal_documents_result 参数错误，你应该在接下来的编码中调用 call_api 重新获得结果，然后传入 filter_legal_docs 函数，写在一个python脚本中
""")
        return []


# /get_sub_company_info_list|filter_sub_company
# 子公司过滤辅助函数,输入关联上市公司全称 金额范围 持股范围 可以通过市公司投资金额和上市公司参股比例筛选子公司
def filter_sub_company(sub_company_list, filter_dict):
    """
    过滤子公司信息
    :param sub_company_list:  /get_sub_company_info_list 返回的结果
    :param filter_dict: dict 包含过滤参数的字典
        - 最小投资金额: str 最小上市公司投资金额（例如 "1亿", "500万"）默认为 -1
        - 最大投资金额: str 最大上市公司投资金额（例如 "1亿", "500万"）默认为inf
        - 最小持股比例: str|int 最小上市公司参股比例，支持 0-100 的百分制，默认为0
        - 最大持股比例: str|int 最大上市公司参股比例，支持 0-100 的百分制，默认为100
        注意：字段只有在需要的时候才存在，例如筛选全资子公司只需要:{'最小持股比例':100}，没有其他字段。
            特别的，最小上市公司投资金额为大于，其余都包含等于，例如：{'最小上市公司投资金额':0} 会筛选大于0的
    :return: list[dict] 包含符合条件的子公司信息的列表，每个子公司信息以字典形式表示
    """
    if not set(filter_dict.keys()) < {"最小投资金额", "最大投资金额", "最小持股比例", "最大持股比例"}:
        print(
            "Traceback:请仔细阅读文档，你的过滤条件不支持,你可以过滤的条件key为:'最小投资金额','最大投资金额','最小持股比例','最大持股比例' 请阅读文档后重新调用或自己实现筛选"
        )
        return []
    try:
        if set(filter_dict.keys()) == {"最小持股比例"} and int(filter_dict["最小持股比例"]) == 0:
            return sub_company_list
        amount_min = filter_dict.get("最小投资金额", -1)
        amount_max = filter_dict.get("最大投资金额", float("inf"))
        holding_ratio_min = filter_dict.get("最小持股比例", 0)
        holding_ratio_max = filter_dict.get("最大持股比例", 100)
        amount_min = map_str_to_num(amount_min)
        amount_max = map_str_to_num(amount_max)
        holding_ratio_min = map_str_to_num(holding_ratio_min)
        holding_ratio_max = map_str_to_num(holding_ratio_max)
        filter_list = []
        for i in sub_company_list:
            raw_info = deepcopy(i)
            i["上市公司投资金额"] = map_str_to_num(i["上市公司投资金额"])
            i["上市公司参股比例"] = int(float(str(i["上市公司参股比例"]).rstrip("%")))
            if (
                amount_min < i["上市公司投资金额"] <= amount_max
                and holding_ratio_min <= i["上市公司参股比例"] <= holding_ratio_max
            ):
                filter_list.append(raw_info)
        print("过滤后的结果为:", filter_list)
        return filter_list
    except KeyError as e:
        print(f"""Traceback:你在之前没有获取{e}这个字段，请先获取此字段再来过滤""")
        return []
    except Exception as e:
        print(f"""
Traceback:
{e}
你的参数错误或者是查询结果有问题，请按照以下方式排查：
判断输入参数是否正确，
  - sub_company_list: 你之前获取的子公司信息的列表，必须包含筛选字段，如果你不确定，你可以获取所有字段后再来过滤
  - filter_dict: 你的过滤条件，是一个字典，如下所示：：{{"最小投资金额":"str", "最小投资金额":"str"}} 可以省略不必要的字段，或者将不必要的字段填空。
你当前的参数为：
sub_company_list: {sub_company_list[:3]} # 只显示前三条    
filter_dict: {filter_dict} 
请分析原因，如果是 sub_company_list 参数错误，你应该在接下来的编码中调用 call_api 重新获得结果，然后传入 filter_sub_company 函数，写在一个 Python 脚本中    
""")

        return []


# /get_xzgxf_info_list|filter_xzgxf_info_list
# 限制高消费过滤函数，支持将 /get_xzgxf_info_list的结果传入并按照条件过滤
def filter_xzgxf_info_list(xzgxf_info_list, filter_dict):
    """
    过滤限制高消费信息列表
    :param xzgxf_info_list: list[dict] 包含行政限高信息的列表
    :param filter_dict: dict 包含过滤条件的字典
        - 审理省份: str 案件审理的省份，注意是简称，例如 安徽省->皖 四川->川
        - 立案时间: str 案件的立案时间年份，例如 '2019'
        - 限高发布日期: str 限高的发布日期年份，例如 '2019'
        - 最小涉案金额: str 默认 "-1" 采用的是大于 例如 输入 ”0“ 则筛选涉案金额大于0，支持 "1万"，”1亿“，不支持汉字的 ”一万“
        - 最大涉案金额: str 默认 "inf" 采用的是小于
    注意：字段只有在需要的时候才存在，例如筛选2020年再安徽立案的案件只需要：{'立案时间':'2020','审理省份':'皖'}
    :return: list[dict] 包含符合条件的行政限高信息的列表
    """
    if not set(filter_dict.keys()) < {"审理省份", "立案时间", "限高发布日期", "最小涉案金额", "最大涉案金额"}:
        print(
            "Traceback:请仔细阅读文档，你的过滤条件不支持,你可以过滤的条件key为:'审理省份','立案时间','限高发布日期','最小涉案金额','最大涉案金额' 请阅读文档后重新调用或自己实现筛选"
        )
        return []
    try:
        if isinstance(xzgxf_info_list, dict):
            xzgxf_info_list = [xzgxf_info_list]
        if "审理省份" in filter_dict and filter_dict["审理省份"]:
            xzgxf_info_list = [i for i in xzgxf_info_list if filter_dict["审理省份"] in i["案号"]]
        if "立案时间" in filter_dict and filter_dict["立案时间"]:
            xzgxf_info_list = [i for i in xzgxf_info_list if i["立案日期"].startswith(filter_dict["立案时间"])]
        if "限高发布日期" in filter_dict and filter_dict["限高发布日期"]:
            xzgxf_info_list = [i for i in xzgxf_info_list if i["限高发布日期"].startswith(filter_dict["限高发布日期"])]
        if "最小涉案金额" in filter_dict:
            min_case = map_str_to_num(filter_dict.get("最小涉案金额", -1))
            xzgxf_info_list = [i for i in xzgxf_info_list if map_str_to_num(i["涉案金额"]) > min_case]
        if "最大涉案金额" in filter_dict:
            max_case = map_str_to_num(filter_dict.get("最大涉案金额", float("inf")))
            xzgxf_info_list = [i for i in xzgxf_info_list if map_str_to_num(i["涉案金额"]) < max_case]
        if xzgxf_info_list:
            print("查询结果为:", xzgxf_info_list)
            return xzgxf_info_list
        else:
            raise ValueError("过滤结果为空")
    except KeyError as e:
        print(f"""Traceback:你在之前没有获取{e}这个字段，请先获取此字段再来过滤""")
        return []
    except Exception as e:
        print(f"""
Traceback:
{e}
你的参数错误或者是查询结果有问题，请按照以下方式排查：
判断输入参数是否正确，
  - xzgxf_info_list: 你之前获取的限制高消费信息，必须包含筛选字段，如果你不确定，你可以获取所有字段后再来过滤
  - param：阅读函数文档，确定参数，如果参数在范围内，请你修改为正确的格式，如果函数无法实现你想要的功能，则自己实现，
  - param: 你的过滤条件，是一个字典，如下所示：{{"审理省份":"皖", "立案时间":"2019", "限高发布日期":"2019"}} 可以省略不必要的字段，或者将不必要的字段填空。
你当前的参数为：
xzgxf_info_list: {xzgxf_info_list[:3]} # 只显示前三条    
filter_dict: {filter_dict}
请分析原因，如果是 xzgxf_info_list 参数错误，你应该在接下来的编码中调用 call_api 重新获得结果，然后传入 filter_xzgxf_info_list 函数，写在一个 Python 脚本中
另外，如果你有一些其他的过滤条件，你可以仿照 filter_xzgxf_info_list 函数的做法，自行书写。    
""")
        return []


# 级别.*法院|法院.*级别|sort_court_level
# 将法院按照从高到低进行排序
def sort_court_level(case_num_list, level_type="法院级别"):
    """
    :param case_num_list: list[dict] or list 案号列表或者 [{"案号":str}],可以直接传入接口结果
    :param level_type: 法院级别 或者 行政级别
    :return:List[Dict['案号','法院名称']] 排序后的结果
    """
    if isinstance(case_num_list[0], dict) and "案号" in case_num_list[0]:
        case_num_list = [i["案号"] for i in case_num_list]
    court_list = []
    for i in case_num_list:
        with contextlib.redirect_stdout(io.StringIO()):
            data = get_court_code_by_case_number({"query_conds": {"案号": i}, "need_fields": []})
        data = {"案号": i, "法院名称": data["法院名称"], level_type: data[level_type]}
        court_list.append(data)
    if level_type == "法院级别":
        court_level_dic = {"基层法院": 1, "中级法院": 2, "高级法院": 3}
    else:
        court_level_dic = {"区县级": 1, "市级": 2, "省级": 3}
    court_list = [i for i in court_list if i[level_type]]
    court_list = sorted(court_list, key=lambda x: court_level_dic.get(x[level_type], 4), reverse=True)
    print("排序结果为:", court_list)
    return court_list


# .
# 可以转化字符串成数字
def map_str_to_num(str_num):
    if not isinstance(str_num, str):
        return str_num
    try:
        str_num = str_num.replace("千", "*1e3")
        str_num = str_num.replace("万", "*1e4")
        str_num = str_num.replace("亿", "*1e8")
        return eval(str_num)
    except:
        pass
    return -100
