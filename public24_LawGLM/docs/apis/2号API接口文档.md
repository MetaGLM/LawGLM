## 2 号API接口函数 	根据统一社会信用代码查询公司名称

``` 
def get_company_register_name(query_conds: dict,need_fields: List[str] = []) -> str:
    """
    根据统一社会信用代码查询公司名称。

    参数:
    query_conds -- 查询条件字典，例如{"统一社会信用代码": "913305007490121183"}
    
    例如：
        输入：
        {"query_conds": {"统一社会信用代码": "913305007490121183"}}
        输出：
        {'公司名称': '天能电池集团股份有限公司'}
    """
    url = f"https://{DOMAIN}/law_api/s1_b/get_company_register_name"

    data = {
        "query_conds": query_conds,
        "need_fields": need_fields
    }

    rsp = requests.post(url, json=data, headers=headers)
    
    return rsp.json()
``` 

### 例子： 
### 公司全称
##### 输入
``` 
{"统一社会信用代码": "913305007490121183"}
``` 
#### 输出 
``` 
{'公司名称': '天能电池集团股份有限公司'}

```
### 公司简称
#### 输入
``` 
{"统一社会信用代码": "913310007200456372"}
``` 
#### 输出
``` 
{'公司名称': '浙江百达精工股份有限公司'}
``` 


### 公司代码
#### 输入
``` 
{"统一社会信用代码": "91320722MA27RF9U87"}
``` 
#### 输出
``` 
{'公司名称': '东海县万德斯环保科技有限责任公司'}
``` 
