## 4 号API接口函数 根据公司的统一社会信用代码查询公司名称

``` 
def get_company_register_name_service(Uniform_social_redit_code: Annotated[str, "公司的统一社会信用代码", True]) -> str:
    """
     根据公司的统一社会信用代码查询公司名称,注意统一社会信用代码为18位字符串。

    参数:
    Uniform_social_redit_code -- 统一社会信用代码，例如"913305007490121183
    
    例如：
        输入：
        Uniform_social_redit_code = "913305007490121183"
        输出：
        {'公司名称': '天能电池集团股份有限公司'}
    """
``` 

### 例子： 
### 1
##### 输入
``` 
Uniform_social_redit_code="913310007200456372"
``` 
#### 输出 
``` 
{"公司名称": "浙江百达精工股份有限公司"}

```
### 2
#### 输入

Uniform_social_redit_code="91420100568359390C"
``` 
输出
{"公司名称": "武汉光庭信息技术股份有限公司"}
``` 


### 3
#### 输入
``` 
Uniform_social_redit_code="91370000164102345T"
``` 

#### 输出
``` 
'{"公司名称": "上海妙可蓝多食品科技股份有限公司"}'
``` 
