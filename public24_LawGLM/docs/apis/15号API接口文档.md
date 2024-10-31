## 15号API接口函数 	根据案号查询限制高消费相关信息
``` 
def get_xzgxf_info(query_conds: dict,need_fields: List[str] = []) -> dict:
    """
    根据案号查询限制高消费相关信息。

    参数:
    query_conds -- 查询条件字典，例如{"案号": "（2018）鲁0403执1281号"}
    need_fields -- 需要返回的字段列表，例如["限制高消费企业名称","案号","法定代表人","申请人","涉案金额","执行法院","立案日期","限高发布日期"],need_fields传入空列表，则表示返回所有字段，否则返回填入的字段

    例如：
        输入：
        {"案号": "（2018）鲁0403执1281号"}
        输出：
        {'限制高消费企业名称': '枣庄西能新远大天然气利用有限公司',
        '案号': '（2018）鲁0403执1281号',
        '法定代表人': '高士其',
        '申请人': '枣庄市人力资源和社会保障局',
        '涉案金额': '12000',
        '执行法院': '山东省枣庄市薛城区人民法院',
        '立案日期': '2018-11-16 00:00:00',
        '限高发布日期': '2019-02-13 00:00:00'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_xzgxf_info"
    case_num = query_conds['案号']
    if isinstance(case_num, str):
        case_num = case_num.replace('（', '(').replace('）', ')')

    if isinstance(case_num, list):
        new_case_num = []
        for ele in case_num:
            new_case_num.append(ele.replace('（', '(').replace('）', ')'))
        case_num = new_case_num
    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    return rsp.json()

``` 

### 例子： 
### 1
#### 输入
``` 
{"案号": "（2018）鲁0403执1281号"", "need_fields":["限制高消费企业名称","案号","法定代表人","申请人","涉案金额","执行法院","立案日期","限高发布日期"]}
``` 
#### 输出 
``` 
{'限制高消费企业名称': '枣庄西能新远大天然气利用有限公司',
        '案号': '（2018）鲁0403执1281号',
        '法定代表人': '高士其',
        '申请人': '枣庄市人力资源和社会保障局',
        '涉案金额': '12000',
        '执行法院': '山东省枣庄市薛城区人民法院',
        '立案日期': '2018-11-16 00:00:00',
        '限高发布日期': '2019-02-13 00:00:00'}

```
