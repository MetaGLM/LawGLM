from Agent.llm import llm, super_eval
from knowledge.tools import *


def get_company_info(company):
    company = company.replace('的法人', '').replace('法人', '')
    route = '/get_company_info'
    query_conds = {"公司名称": company}
    need_fields = ["法人代表", "注册地址", "联系电话", "总经理", "董秘"]
    param = {"query_conds": query_conds, "need_fields": need_fields}
    requirement = ""
    company_details_result = call_api(route, param, requirement)
    return company_details_result


def get_lawfirm_info(lawfirm):
    route = '/get_lawfirm_info'
    query_conds = {"律师事务所名称": lawfirm}
    need_fields = ["通讯电话"]
    param = {"query_conds": query_conds, "need_fields": need_fields}
    requirement = "获取江苏义科律师事务所的联系电话"
    lawfirm_phone = call_api(route, param, requirement)
    return lawfirm_phone


def write_qisuzhuang(param):
    base_info = {'诉讼请求': param['案由'], '起诉日期': param['时间'], '法院名称': param['法院'], '证据': '-',
                 '事实和理由': '-'}
    yuan_info = get_company_info(param['原告'])
    if '法人' in param['原告']:
        base_info.update(
            {'原告': yuan_info['法人代表'], '原告性别': '-', '原告民族': '-', '原告生日': '-',
             '原告地址': yuan_info['注册地址'], '原告联系方式': yuan_info['联系电话'],
             '原告工作单位': param['原告'].replace('法人', '')}
        )
    elif '总经理' in param['原告']:
        base_info.update(
            {'原告': yuan_info['总经理'], '原告性别': '-', '原告民族': '-', '原告生日': '-',
             '原告地址': yuan_info['注册地址'], '原告联系方式': yuan_info['联系电话'],
             '原告工作单位': param['原告'].replace('总经理', '')}
        )
    elif '董秘' in param['原告']:
        base_info.update(
            {'原告': yuan_info['董秘'], '原告性别': '-', '原告民族': '-', '原告生日': '-',
             '原告地址': yuan_info['注册地址'], '原告联系方式': yuan_info['联系电话'],
             '原告工作单位': param['原告'].replace('董秘', '')}
        )
    else:
        base_info.update(
            {'原告': param['原告'], '原告法定代表人': yuan_info['法人代表'], '原告地址': yuan_info['注册地址'],
             '原告联系方式': yuan_info['联系电话']}
        )
    bei_info = get_company_info(param['被告'])
    if '法人' in param['被告']:
        base_info.update(
            {'被告': bei_info['法人代表'], '被告性别': '-', '被告民族': '-', '被告生日': '-',
             '被告地址': bei_info['注册地址'], '被告联系方式': bei_info['联系电话'],
             '被告工作单位': param['被告'].replace('法人', '')}
        )
    elif '总经理' in param['被告']:
        base_info.update(
            {'被告': yuan_info['总经理'], '被告性别': '-', '被告民族': '-', '被告生日': '-',
             '被告地址': yuan_info['注册地址'], '被告联系方式': yuan_info['联系电话'],
             '被告工作单位': param['被告'].replace('总经理', '')}
        )
    elif '董秘' in param['被告']:
        base_info.update(
            {'被告': yuan_info['董秘'], '被告性别': '-', '被告民族': '-', '被告生日': '-',
             '被告地址': yuan_info['注册地址'], '被告联系方式': yuan_info['联系电话'],
             '被告工作单位': param['被告'].replace('董秘', '')}
        )
    else:
        base_info.update(
            {'被告': param['被告'], '被告法定代表人': bei_info['法人代表'], '被告地址': bei_info['注册地址'],
             '被告联系方式': bei_info['联系电话']}
        )
    yuan_l = get_lawfirm_info(param['原告律师事务所'])
    base_info.update({'原告委托诉讼代理人': yuan_l['律师事务所名称'], '原告委托诉讼代理人联系方式': yuan_l['通讯电话']})
    bei_l = get_lawfirm_info(param['被告律师事务所'])
    base_info.update({'被告委托诉讼代理人': bei_l['律师事务所名称'], '被告委托诉讼代理人联系方式': bei_l['通讯电话']})
    e1 = 'citizens' if ('法人' in param['原告'] or '法人' in param['原告'] or '董秘' in param['原告']) else 'company'
    e2 = 'citizens' if ('法人' in param['被告'] or '法人' in param['被告'] or '董秘' in param['被告']) else 'company'
    route = f'/get_{e1}_sue_{e2}'
    return call_api(route, base_info)['doc']


def qisuzhuang_flow(question):
    prompt = '''
我有一个题目，我需要整理成一个字典格式的json，字典格式如下：
```
{
    "原告": "",
    "被告": "",
    "原告律师事务所": "",
    "被告律师事务所": "",
    "时间": "",
    "法院": "",
    "案由": ""
}
```
例如题目：大唐华银电力股份有限公司法人与上海现代制药股份有限公司发生了民事纠纷，大唐华银电力股份有限公司委托给了北京国旺律师事务所，上海现代制药股份有限公司委托给了北京浩云律师事务所，请写一份民事起诉状给天津市蓟州区人民法院时间是2024-02-01，注：法人的地址电话可用公司的代替。

你应该返回json格式的：
```json
{
    "原告": "大唐华银电力股份有限公司法人",
    "被告": "上海现代制药股份有限公司",
    "原告律师事务所": "北京国旺律师事务所",
    "被告律师事务所": "北京浩云律师事务所",
    "时间": "2024-02-01",
    "法院": "天津市蓟州区人民法院",
    "案由": "民事纠纷"
}

```
你需要注意的是起诉和被起诉的是公司还是公司法人,总经理，董秘.
如果不是示例格式的题目，即不是要求书写起诉书，请不要整理json，直接返回：题目格式错误。
'''

    param = llm([{'role': 'system', 'content': prompt}, {'role': 'user', 'content': question}])

    if '```json' in param:
        param = super_eval(param)
        res = write_qisuzhuang(param)
        return res
    else:
        return None


def map_str_to_num(str_num):
    try:
        str_num = str_num.replace("千", "*1e3")
        str_num = str_num.replace("万", "*1e4")
        str_num = str_num.replace("亿", "*1e8")
        return eval(str_num)
    except Exception as e:

        pass
    return -100


def get_legal_doc(company_name, param):
    return_dict = {}

    if param['工商信息']['是否需要']:

        info = call_api('/get_company_register', {"query_conds": {"公司名称": company_name}, "need_fields": []})
        for i in param['工商信息']['不需要字段']:
            if i in ['公司简介']:
                i = '企业简介'
            del info[i]
        return_dict['工商信息'] = [info]
    else:
        return_dict['工商信息'] = []
    sub_company_list = call_api('/get_sub_company_info_list',
                                {"query_conds": {"关联上市公司全称": company_name}, "need_fields": []})
    # print(param['子公司信息'])
    param['子公司信息'].get('过滤条件', {}).get('最小金额', -1)
    sub_company_param = {
        '最小持股比例': param['子公司信息'].get('过滤条件', {}).get('最小参股比例', 0),
        '最小投资金额': param['子公司信息'].get('过滤条件', {}).get('最小参股比例', 0)
    }
    if param['子公司信息']['是否需要']:

        return_dict['子公司信息'] = filter_sub_company(sub_company_list, sub_company_param)
    else:
        return_dict['子公司信息'] = []
    if '裁判文书' in param and param['裁判文书']['是否需要']:
        use_company = [company_name]
        if param['裁判文书']['是否包含子公司']:
            use_company.extend([i['公司名称'] for i in sub_company_list])
        out = param['裁判文书'].get('不需要字段', [])
        legal_documents_param = {
            '最小涉案金额': param['裁判文书'].get('过滤条件', {}).get('最小金额', -1),
            '年份类型': param['裁判文书'].get('过滤条件', {}).get('年份类型', None),
            '年份': param['裁判文书'].get('过滤条件', {}).get('年份', None)
        }

        info = []
        for company in use_company:
            try:
                print(company)
                legal_documents_result = call_api('/get_legal_document_list',
                                                  {"query_conds": {"关联公司": company},
                                                   "need_fields": []})
                if isinstance(legal_documents_result, dict):
                    legal_documents_result = [legal_documents_result]

                for i in legal_documents_result:
                    for j in out:
                        if j in i:
                            del i[j]
                    # del i['判决结果']
                    info.append(i)
            except:
                ...

        return_dict['裁判文书'] = filter_legal_docs(info, legal_documents_param)
    else:
        return_dict['裁判文书'] = []
    if '限制高消费' in param and param['限制高消费']['是否需要']:
        legal_documents_param = {
            '最小涉案金额': param['裁判文书'].get('过滤条件', {}).get('最小金额', -1),
            '年份类型': param['裁判文书'].get('过滤条件', {}).get('年份类型', None),
            '年份': param['裁判文书'].get('过滤条件', {}).get('年份', None)
        }
        info = []
        use_company = [company_name]
        if param['限制高消费']['是否包含子公司']:
            use_company.extend([i['公司名称'] for i in sub_company_list])
        out = param['限制高消费'].get('不需要字段', [])
        for company in use_company:
            try:
                print(company)
                legal_documents_result = call_api('/get_xzgxf_info_list',
                                                  {"query_conds": {"限制高消费企业名称": company},
                                                   "need_fields": []}, print_str=False)
                if isinstance(legal_documents_result, dict):
                    legal_documents_result = [legal_documents_result]

                for i in legal_documents_result:
                    for j in out:
                        if j in i:
                            del i[j]
                    info.append(i)

            except:
                ...
        return_dict['限制高消费'] = filter_xzgxf_info_list(info, legal_documents_param)
    else:
        return_dict['限制高消费'] = []
    return return_dict


def zhenghebaogao_flow(question):
    prompt = '''
我有一个，题目，我需要整理成一个字典格式的json，字典格式如下：

### 通用JSON格式
```json
{
    "公司名称": "str",
    "报告参数": {
        "工商信息": {
            "是否需要": true,
            "不需要字段": ["str"]
        },
        "子公司信息": {
            "是否需要": true,
            "不需要字段": ["str"],
            "是否需要子公司": true,
            "过滤条件": {
                "最小金额": "str",
                "最小参股比例": "str"
            }
        },
        "裁判文书": {
            "是否需要": true,
            "不需要字段": ["str"],
            "是否包含子公司":true,
            "过滤条件": {
                "最小金额": "str",
                "年份": "str",
                "年份类型": "str"
            }
        },
        "限制高消费": {
            "是否需要": true,
            "不需要字段": ["str"],
            "是否包含子公司":true,
            "过滤条件": {
                "最小金额": "str",
                "年份": "str",
                "年份类型": "str"
            }
        }
    }
}
```

### 说明

#### 顶层字段
- **公司名称**: 公司名称，字符串类型。例如 `"深圳市瑞丰光电子股份有限公司"`。

#### 报告参数
- **报告参数**: 包含各类报告的参数设置。

#### 工商信息
- **是否需要**: 是否需要工商信息，布尔类型。`true` 表示需要，`false` 表示不需要。
- **不需要字段**: 不需要包含的字段，字符串数组。例如 `["公司简介"]`。

#### 子公司信息
- **是否需要**: 是否需要子公司信息，布尔类型。`true` 表示需要，`false` 表示不需要。
- **不需要字段**: 不需要包含的字段，字符串数组。例如 `[]`。
- **是否需要子公司**: 是否需要子公司，布尔类型。`true` 表示需要，`false` 表示不需要。
- **过滤条件**: 子公司信息的过滤条件设置。
  - **最小金额**: 子公司投资金额的最小值，字符串类型。例如 `"1亿"`。
  - **最小参股比例**: 子公司参股比例的最小值，字符串类型。例如 `"100%"`。

#### 裁判文书
- **是否需要**: 是否需要裁判文书信息，布尔类型。`true` 表示需要，`false` 表示不需要。
- **不需要字段**: 不需要包含的字段，字符串数组。例如 `[]`。
- **是否包含子公司**: 裁判文书信息是否包含子公司，布尔类型。`true` 表示需要，`false` 表示不需要。
- **过滤条件**: 裁判文书的过滤条件设置。
  - **最小金额**: 涉案金额的最小值，字符串类型。例如 `"1万"`。
  - **年份**: 年份，字符串类型。例如 `"2020"`。
  - **年份类型**: 年份类型，字符串类型。例如 `"审理时间"`。

#### 限制高消费
- **是否需要**: 是否需要限制高消费信息，布尔类型。`true` 表示需要，`false` 表示不需要。
- **不需要字段**: 不需要包含的字段，字符串数组。例如 `[]`。
- **是否包含子公司**: 限制高消费信息是否包含子公司，布尔类型。`true` 表示需要，`false` 表示不需要。
- **过滤条件**: 限制高消费的过滤条件设置。
  - **最小金额**: 涉案金额的最小值，字符串类型。例如 `"1万"`。
  - **年份**: 年份，字符串类型。例如 `"2019"`。
  - **年份类型**: 年份类型，字符串类型。例如 `"立案日期"`。

请确保的json不会遗漏任何一个字段，如果没有提及，设为false

### 示例
以下是一个具体的示例：
深圳市瑞丰光电子股份有限公司关于工商信息（不包括公司简介）及投资金额过亿的全资子公司，母公司及子公司的审理时间在2020年涉案金额大于10万的裁判文书（不需要判决结果）以及限制高消费整合报告。

```json
{
    "公司名称": "深圳市瑞丰光电子股份有限公司",
    "报告参数": {
        "工商信息": {
            "是否需要": true,
            "不需要字段": ["公司简介"]
        },
        "子公司信息": {
            "是否需要": true,
            "不需要字段": [],
            "是否需要子公司": true,
            "过滤条件": {
                "最小金额": "1亿",
                "最小参股比例": "100%"
            }
        },
        "裁判文书": {
            "是否需要": true,
            "不需要字段": [],
            "是否包含子公司":true,
            "过滤条件": {
                "最小金额": "10万",
                "年份": "2020",
                "年份类型": "审理时间"
            }
        },
        "限制高消费": {
            "是否需要": true,
            "不需要字段": [],
            "是否包含子公司":true,
            "过滤条件": {
                "最小金额": "10万",
                "年份": "2020",
                "年份类型": "审理时间"
            }
        }
    }
}
```
另外，如果不是示例中的格式，请不要整理json，直接返回：题目格式错误。

'''

    param = llm([{'role': 'system', 'content': prompt}, {'role': 'user', 'content': question}])

    if '```json' in param:
        param = super_eval(param)
        res = get_legal_doc(param['公司名称'], param['报告参数'])
        data = call_api('/save_dict_list_to_word',
                        {'company_name': param['公司名称'], 'dict_list': str(res)})['doc']

        return data
    else:
        return None
