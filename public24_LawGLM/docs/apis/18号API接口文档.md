## 18 号API接口函数 排序接口，返回按照values排序的keys

``` 
def rank(keys: List[Any], values: List[float], is_desc: bool = False):
    '''
    排序接口，返回按照values排序的keys

    参数:
    keys -- 
    values -- 
    is_desc -- 
    '''
    return [i[0] for i in sorted(zip(keys, values), key=lambda x: x[1], reverse=is_desc)]
``` 

### 例子： 
### 1
##### 输入
``` 
{"公司名称": "上海妙可蓝多食品科技股份有限公司","need_fields": ["公司名称", "公司代码", "主营业务"]}
``` 
#### 输出 
``` 
{'公司名称': '上海妙可蓝多食品科技股份有限公司',
 '公司代码': '600882',
 '主营业务': '以奶酪、液态奶为核心的特色乳制品的研发、生产和销售，同时公司也从事以奶粉、黄油为主的乳制品贸易业务。'}

```
### 2
#### 输入

{"公司简称": "海天精工","need_fields":["公司名称", "法人代表", "主营业务","办公地址","联系电话"] }
``` 
输出
{'公司名称': '宁波海天精工股份有限公司',
 '法人代表': '张静章',
 '主营业务': '高端数控机床的研发、生产和销售',
 '办公地址': '浙江省宁波市北仑区黄山西路235号',
 '联系电话': '0574-86188839'}
``` 


### 3
#### 输入
``` 
{"公司代码": "600882","need_fields":["公司名称", "公司简称", "主营业务","办公地址","联系电话"] }
``` 

#### 输出
``` 
{'公司名称': '上海妙可蓝多食品科技股份有限公司',
 '公司简称': '妙可蓝多',
 '主营业务': '以奶酪、液态奶为核心的特色乳制品的研发、生产和销售，同时公司也从事以奶粉、黄油为主的乳制品贸易业务。',
 '办公地址': '上海市浦东新区金桥路1398号金台大厦10楼',
 '联系电话': '021-50188700'}
``` 
