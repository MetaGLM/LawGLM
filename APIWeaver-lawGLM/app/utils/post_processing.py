import re
from datetime import datetime


def convert_date_format(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, "%Y年%m月%d号")
        except ValueError:
            try:
                date_obj = datetime.strptime(date_str, "%Y年%m月%d号")
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, "%Y年%m月%d日")
                except ValueError:
                    return date_str

    formatted_date = date_obj.strftime("%Y年%m月%d日")
    return formatted_date


def convert_dates_in_text(text):
    # 定义正则表达式匹配日期格式
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # 2020-01-01
        r"\d{4}年\d{2}月\d{1,2}号",  # 2020年01月1号
        r"\d{4}年\d{1,2}月\d{1,2}号",  # 2020年1月1号
        r"\d{4}年\d{2}月\d{2}号",  # 2020年01月01号
        r"\d{4}年\d{1,2}月\d{1,2}日",  # 2020年1月1日
    ]

    # 合并所有模式
    combined_pattern = "|".join(date_patterns)

    # 定义替换函数
    def replace_date(match):
        date_str = match.group(0)
        return convert_date_format(date_str)

    # 使用正则表达式替换所有匹配的日期
    result_text = re.sub(combined_pattern, replace_date, text)

    return result_text


import re


def correct_text_errors(question, answer):
    # 正则表达式，匹配保留小数位数的要求
    decimal_pattern = r"(\d+|一|二|三|四|两)位小数"
    num_to_chinese = {"一": 1, "二": 2, "三": 3, "四": 4, "两": 2}

    # 从问题部分获取小数位数要求
    decimal_match = re.search(decimal_pattern, question)
    if decimal_match:
        decimal_request = decimal_match.group(1)
        places = num_to_chinese.get(decimal_request, int(decimal_request) if decimal_request.isdigit() else 0)
    else:
        return answer
        # places = 2  # 默认小数位数，如果没有特别说明

    # 正则表达式，匹配金额和单位
    money_pattern = r"(\d+(\.\d+)?)(元|亿|万)"

    # 用于转换和格式化数字
    def correct_decimal(match):
        number = float(match.group(1))
        unit = match.group(3)
        new_number = round(number, places)
        if unit == "元":
            converted_number = number / 10000
            return f"{new_number:.{places}f}元（{converted_number:.{places}f}万元）"
        else:
            return f"{new_number:.{places}f}{unit}"

    # 应用正则表达式和转换函数到答案部分
    corrected_answer = re.sub(money_pattern, correct_decimal, answer)

    return corrected_answer


# # 测试用例
# questions_answers = [
#     ("请保留三位小数。", "该公司投资的子公司有5家，投资总额为1737995000元。"),
#     ("请保留四位小数。", "陕西建设机械股份有限公司的注册资本为12.5711111亿元。"),
#     ("请保留一位小数。", "投资总额为1737995000.0元。"),
#     ("请保留二位小数。", "该公司的年营业额为500000万元。")
# ]
#
# # 应用函数并打印结果
# for question, answer in questions_answers:
#     corrected_answer = correct_text_errors(question, answer)
#     print(f"Question: {question}\nOriginal Answer: {answer}\nCorrected Answer: {corrected_answer}\n")


def add_bracket_content(match):
    # 提取匹配的数字和单位
    num = match.group(1)
    unit = match.group(2)

    # 将字符串数字转换为浮点数，然后根据是否有非零小数部分来决定格式化方式
    formatted_num = float(num)
    # 检查数字是否为整数（没有小数部分）
    formatted_num_str = f"{formatted_num:.0f}" if formatted_num.is_integer() else num

    # 生成新的字符串，仅当数字格式有变化时添加括号内容
    if formatted_num_str != num:
        new_string = f"{formatted_num_str}{unit}（{formatted_num_str}{unit}）"
    else:
        new_string = f"{num}{unit}"
    return new_string


def mach_nums(text):
    pattern = re.compile(r"([0-9]+\.[0-9]+|\d+)(亿|万|元)")
    new_text = pattern.sub(add_bracket_content, text)
    return new_text


def format_answer(question, answer):
    answer = convert_dates_in_text(answer)
    answer = (
        answer.replace(" ", "").replace("**", "").replace("℃", "度").strip('"').replace("（", "(").replace("）", ")")
    )
    answer = re.sub(r"(\d{1,3})(,\d{3})*", lambda x: x.group().replace(",", ""), answer)
    if "位小数" in question:
        answer = correct_text_errors(question, answer)
    else:
        answer = mach_nums(answer)

    dic = {
        "一个": "1个",
        "两个": "2个",
        "三个": "3个",
        "四个": "4个",
        "五个": "5个",
        "六个": "6个",
        "七个": "7个",
        "八个": "8个",
        "九个": "9个",
        "一家": "1家",
        "两家": "2家",
        "三家": "3家",
        "四家": "4家",
        "五家": "5家",
        "六家": "6家",
        "七家": "7家",
        "八家": "8家",
        "九家": "9家",
        "第一": "第1",
        "第二": "第2",
        "第三": "第3",
        "第四": "第4",
        "第五": "第5",
        "第六": "第6",
        "【": "(",
        "】": ")",
    }

    for k, v in dic.items():
        answer = answer.replace(k, v)

    return answer


if __name__ == "__main__":
    q = "(2020)吉0184民初5156号的被告是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？该公司是否被限制高消费？如果是被限制高消费的涉案金额总额为？请保留两位小数"
    a = "(2020)吉0184民初5156号案件的被告是武汉敦煌种业有限公司，该公司不是上市公司。其统一社会信用代码为91420100768057426X。该公司被限制高消费，涉案金额总额为476.000元"
    x = format_answer(q, a)

    print(x)
