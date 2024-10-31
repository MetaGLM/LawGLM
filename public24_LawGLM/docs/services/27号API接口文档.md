## 27号API接口函数 根据案号返回法院名称 

``` 
def get_court_code_service_by_reference(reference: Annotated[str, "案号", True]) -> str:
    """
    根据案号返回法院名称 

    参数:
    reference -- 案号

    例如：
        输入：
        reference="(2020)渝0112民初27463号"
        输出：
        '"{\\"法院名称\\": \\"重庆市渝北区人民法院\\"}"'
    """
    pattern = re.compile(r'[\u4e00-\u9fa5](\d+)')
    match = pattern.search(reference)
    result = match.group(0) if match else None
    rsp = get_court_code_service(court_name=result,need_fields=["法院名称"])
    json_str = json.dumps(rsp, ensure_ascii=False)
    return json_str
``` 

### 例子： 
### 1
##### 输入
``` 
reference="(2020)渝0112民初27463号"
``` 
#### 输出 
``` 
'"{\\"法院名称\\": \\"重庆市渝北区人民法院\\"}"'

```
### 2
#### 输入
```
reference="(2019)京0101民初11731号"
``` 
输出
'"{\\"法院名称\\": \\"北京市东城区人民法院\\"}"'
``` 


### 3
#### 输入
``` 
"涉诉案号(2019)京0101民初17740号让我有点烦恼"
``` 

#### 输出
``` 
'"{\\"法院名称\\": \\"北京市东城区人民法院\\"}"'
``` 
