import requests
import re
from knowledge.priori import ERROR_TIPS
from fuzzywuzzy import fuzz
import json
from utils.arg_utils import judge_param, convert_date_format
from collections import defaultdict


def search(route, param):
    return _search(route, param)


DefaultUnit = {
    '涉案金额': '元',
    '注册资本': '万元',
    '参保人数': '人',
    '上市公司投资金额': '万元',
    '事务所注册资本': '元',
    '最高温度': '度',
    '最低温度': '度'
}





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


def rank(data_list, key, is_desc: bool = False):
    pos_kv = []
    for item in data_list:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, str) and re.search(r'\d', value):
            value = map_str_to_num(value)
        elif isinstance(value, str):
            continue
        pos_kv.append((item, value))

    sorted_list = sorted(pos_kv, key=lambda x: x[1], reverse=is_desc)
    return [i[0] for i in sorted_list]


def get_sum(nums):
    if not isinstance(nums, list) or len(nums) == 0:
        return 0
    if any(not isinstance(x, (int, float, str)) for x in nums):
        return 0

    def str_to_num(str_num):
        try:
            str_num = str_num.replace("千", "*1e3")
            str_num = str_num.replace("万", "*1e4")
            str_num = str_num.replace("亿", "*1e8")
            return eval(str_num)
        except:
            return 0

    if isinstance(nums[0], str):
        nums = [str_to_num(i) for i in nums]

    try:
        return sum(nums)
    except:
        return 0


def case_num_search(route, param, depth=0):
    try:
        if depth > 3:
            return '没有查询到内容'

        domain = "comm.chatglm.cn"
        token = 'black_myth_wukong'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        url = f"https://{domain}/law_api/s1_b{route}"
        rsp = requests.post(url, json=param, headers=headers).json()
        if '案号' in rsp:
            return rsp
        if '(' in param['query_conds']['案号'] or ')' in param['query_conds']['案号']:
            param['query_conds']['案号'] = param['query_conds']['案号'].replace('(', '（').replace(')', '）')
            return case_num_search(route, param, depth + 1)
        elif '（' in param['query_conds']['案号'] or '）' in param['query_conds']['案号']:
            param['query_conds']['案号'] = param['query_conds']['案号'].replace('（', '(').replace('）', ')')
            return case_num_search(route, param, depth + 1)
        elif '【' in param['query_conds']['案号'] or '】' in param['query_conds']['案号']:
            param['query_conds']['案号'] = param['query_conds']['案号'].replace('【', '(').replace('】', ')')
            return case_num_search(route, param, depth + 1)

        return '没有查询到内容'
    except:
        return '没有查询到内容'


def _search(route, param):
    if route == '/rank':
        return rank(**param)
    if route == '/get_sum':
        return get_sum(param)
    if isinstance(param, dict) and 'query_conds' in param and '案号' in param['query_conds']:
        return case_num_search(route, param)
    domain = "comm.chatglm.cn"
    token = 'black_myth_wukong'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    url = f"https://{domain}/law_api/s1_b{route}"
    rsp = requests.post(url, json=param, headers=headers)

    with open('log/api_log.jsonl', 'a', encoding='utf8') as f:
        f.write(json.dumps(
            {'route': route,
             'param': param,
             'rsp': rsp.text
             }
        ))
    if re.search('get_.+_sue_|save_dict_list_to_word', route):
        if 'Error' not in rsp.text:
            return {"doc": rsp.text}
        else:
            return rsp.text
    try:
        if not rsp.json():
            return route + '没有查询到内容'

        res = rsp.json()
        if 'list' in route and isinstance(res, dict):
            return [res]

        return res

    except Exception as e:
        return '调用失败，请分析原因'


def format_param(route, param):
    if 'query_conds' in param:
        if param['need_fields']:
            if param['query_conds'].keys() not in param['need_fields']:
                param['need_fields'].extend(list(param['query_conds'].keys()))

            if route == '/get_company_register_name':
                param['need_fields'] = []

        if route == '/get_temp_info':
            if '日期' in param['query_conds']:
                param['query_conds']['日期'] = convert_date_format(param['query_conds']['日期'])

    return route, param


def check_result(route, param, res, requirement):
    if isinstance(res, str):
        if requirement and re.search('是否|判断', requirement):
            print('未查到信息判定为否')
            return {"res": '未查到信息判定为否'}
        tips = ''
        rule_message = False
        for info in ERROR_TIPS:
            if info['pos_route'] == 'ALL' or route in info['pos_route']:
                if not info['use_field']:
                    print('重要提示:', info['content'])
                    tips += f"重要提示:{info['content']}\n"
                    rule_message = True
                else:
                    content_for_tip = ''
                    for field in info['use_field']:
                        if field == 'requirement':
                            content_for_tip += f"{requirement}\n"
                        if field == 'param':
                            if 'query_conds' in param:
                                content_for_tip += f"{json.dumps(param['query_conds'], ensure_ascii=False, indent=4)}\n"

                    if re.search(info['pattern'], content_for_tip, re.DOTALL):
                        print('重要提示:', info['content'])
                        tips += f"重要提示:{info['content']}\n"
                        rule_message = True

        if 'error' in res:
            print('API info:' + res)
            return {'error': '请根据以上信息处理API调用错误，重新调用call_api函数'}

        if not rule_message:  # 没有找到针对的提示
            print('API info:' + res)
        return {'error': '请根据以上信息处理API调用错误，重新调用call_api函数'}
        # return 'API info:'+res

    return {'res': res}


def call_api(route, param, requirement=None, print_str=True):
    if route in ['/rank', '/sum']:
        print_str = False
    if not judge_param(route, param):
        print('参数错误，请按照提示检查错误')
        return
    route, param = format_param(route, param)
    res = _search(route, param)
    check_info = check_result(route, param, res, requirement)
    if 'error' in check_info:
        print(f'''
{check_info['error']}     
你的查询数据库中没有记录，如果不是验证是否存在的查询，请基于以上提示，进行修改。
Traceback:
Error：查询无记录''')
        if 'list' in route:
            return []
        else:
            return defaultdict(str)

    if print_str:
        if isinstance(check_info["res"], list) and len(check_info["res"]) > 3 and len(str(check_info["res"])) > 700:
            print(
                f'{requirement}参数为：{param} 查询结果为:{check_info["res"][:3]} # 只显示前三条 一共{len(check_info["res"])}条，如果题目查看所有的子公司或者案号的需求，请你单独打印。')
        else:
            print(f'{requirement}参数为：{param} 查询结果为:{check_info["res"]}')  # 正确就，打印出信息
    return check_info["res"]


def run_all_api():  # 测试所有接口是否通畅
    from knowledge.api_info import APIS
    for i in APIS:
        print(i['路由'], i['参数示例'])
        call_api(i['路由'], i['参数示例'])
