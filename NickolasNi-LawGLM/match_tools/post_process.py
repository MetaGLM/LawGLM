import json
import ast
from typing import get_origin, Annotated


from model import call_glm
from match_tools.tools_register import register_tool
from match_tools.schema import get_table_properties
from apis.api import augment_company_name, http_api_call_original, http_api_call
from utils import parse_json_from_response
from config import *

# prompt_filter_condition = '''对于复杂的统计型问题的解决思路一般分为"根据条件找出潜在答案的数组集合"再"根据问题中的条件对于潜在答案的数组集合进行过滤"这两步。
# 请根据原始问题和已知的第二步中的数组集合解析出第二步中对数组集合的过滤条件。请直接返回从问题中解析出来的对于法律文书数组集合的过滤条件。不要回答问题之外的内容。
#
# 过滤条件一般分为：
# 1. 对数组元素的字段值进行限制。对于字符串字段只要求包含某字段，不要求等于。比如对于被告或者原告进行限制时，'被告'：'包含**'或者'原告'：'包含**'。
# 2. 对数组元素的字段值进行比较。'涉案金额':'在金额A和金额B之间'。
# 3. 对数组元素的字段值进行排序并获取前N个或第N个。'投资金额':'最高或者第二高'。
#
# 输出格式：
# 被限制字段：限制条件
# example：
# 被告： 包含**公司
# 涉案金额：在100万到200万之间
# 投资金额：第二高
#
# <原始问题>
# {query}
# </原始问题>
#
# <已知信息>
# {provided_information}
# </已知信息>
#
# 对于{target_list}的过滤条件：(不要回答问题)'''


prompt_filter_condition = """对于复杂的统计型问题的解决思路一般分为"根据条件找出潜在答案的数组集合"再"根据问题中的条件对于潜在答案的数组集合进行过滤"这两步。
请根据原始问题、已知信息以及数组元素的key集合，给出对于该数组合计的过滤条件，过滤条件是一个数组，数组元素是键值对，包含key：过滤的键值、operation：过滤操作，value：过滤的值。不要回答问题之外的内容。
除了一些需要过滤的字段，也要考虑某些成为后续问题前提条件的字段，这些字段只有key也就是字段名，operation和value都为空。比如问到'这些案件是在什么地方审理的',需要用到逻辑链:案号、法院代字、法院名称、法院地址,此时需要key:案号。
问题中提到'起诉'需要生成key'原告'的过滤条件。问题中提到'被起诉'需要生成key'被告'的过滤条件。
当问题没有提到'原告'或'被告'，则不能生成key是'原告'或'被告'的过滤条件。
当问到起诉期日则需要对'案号'字段进行过滤，比如要求起诉日期在2020年，则需要'案号'字段包含2020。
如果问到审理日期则需要对'日期'字段进行过滤。
当问到案件原由时则需要对'案由'字段进行过滤,案由的条件需要对问题中的信息进行精简，如'劳务及劳务者相关的纠纷案件'可以精简为案由包含'劳务'.
问题中问到涉案金额总和时对于key涉案金额采用operation是sum，而不需要对涉案金额是否大于0进行限制。
律师事务所的唯一码是律师事务所的一个属性，不是限制条件。

可选择的过滤的键值key有如下：
{keys}

过滤操作operation有如下：
<:小于某值
<=:小于等于某值
>:大于某值
>=:大于等于某值
!=:不等于某值
==: 等于某值
contain:包含某值
!contain:不包含某值
sum:对于某key进行求和，此时的value为空字符串
top:找出字段key的第几高/大，此时的value为int，比如value是1时表示找出key最高，value是2时表示找出key第二高，依次类推
bottom:找出字段key的倒数第几或者第几小，此时的value为int，比如value是1时表示找出key最小或者说倒数第一，value是2时表示找出key第二小或者倒数第二，依次类推
tops:找出字段key的前几高/大，此时的value为int，比如value是5时表示找出前5高的结果，依次类推
bottoms:找出字段key的前第几低/小，此时的value为int，比如value是5时表示找出前5小的结果，依次类推


请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：91310000677833266F的公司全称是？该公司的涉案次数为？（起诉日期在2020年）作为被起诉人的次数及总金额为？
```json
[
    {{"key":"被告","operation":"contain","value":"上海大众汽车有限公司"}},
    {{"key":"案号","operation":"contain","value":"2020"}},
    {{"key":"涉案金额","operation":"sum","value":""}}
]
``` 

example：请帮我查询一下浙江晨丰科技股份有限公司参与的案件有涉案金额的有哪些？涉案金额总和为？
```json
[
    {{"key":"涉案金额","operation":"sum","value":""}}
]
``` 

example：涉案金额第二高的民事初审案件
```json
[
    {{"key":"涉案金额","operation":"top","value":2}},
    {{"key":"案号","operation":"contain","value":"民初"}}
]
``` 

example：株洲宏达恒芯电子有限公司作为原告的案件是在什么地方审理的
```json
[
    {{"key":"原告","operation":"contain","value":"株洲宏达恒芯电子有限公司"}},
    {{"key":"案号","operation":"","value":""}}
]
``` 

example：新特能源股份有限公司的涉诉的涉案金额大于10000元的裁判文书案号有哪些
```json
[
    {{"key":"涉案金额","operation":">","value":"10000"}}
]
``` 

example：河南龙马环境产业有限公司涉及的案件中，立案时间发生于2021年发生的劳务及劳务者相关的纠纷案件有几次？涉案总金额为？案号分别是？
```json
[
    {{"key":"案号","operation":"contain","value":"2021"}},
    {{"key":"案由","operation":"contain","value":"劳务"}},
    {{"key":"涉案金额","operation":"sum","value":""}},
    {{"key":"案号","operation":"","value":""}}
]
``` 

example：立案时间在2019年涉案金额不为0的裁判文书
```json
[
    {{"key":"案号","operation":"contain","value":"2019"}},
    {{"key":"涉案金额","operation":"!=","value":"0"}}
]
``` 

example：审理时间在2020年涉案金额不小于10万的裁判文书
```json
[
    {{"key":"日期","operation":"contain","value":"2020"}},
    {{"key":"涉案金额","operation":">=","value":"10万"}}
]
``` 

有已知信息时要充分考虑到已知信息
example：原告是300077案件审理法院是什么时候成立的
已知信息：根据:300077,查询到:'公司名称': '国民技术股份有限公司', '公司代码_股票代码': '300077'
```json
[
    {{"key":"原告","operation":"contain","value":"国民技术股份有限公司"}},
    {{"key":"案号","operation":"","value":""}}
]
``` 

<原始问题>
{query}
</原始问题>

{provided_information}

过滤条件："""

prompt_filter_condition_get_sub_company_info_list = """对于复杂的统计型问题的解决思路一般分为"根据条件找出潜在答案的数组集合"再"根据问题中的条件对于潜在答案的数组集合进行过滤"这两步。
请根据原始问题中关于子公司数组的子问题、已知信息以及子公司可用于过滤的字段，给出对于子公司数组的过滤条件，过滤条件是一个数组，数组元素是键值对，包含key：过滤的键值、operation：过滤操作，value：过滤的值。不要回答问题之外的内容。
返回的结果中第一个元素是一个字符串用来表示过滤条件之间是交集还是并集，有两个可选：intersection表示数组集合要同时满足所有过滤条件，union表示数组集合要分别满足不同的过滤条件。返回结果后面的元素是过滤条件。如果不需要对数组集合则返回空数组。
注意问题中的错别字,比如'圈资'应为'全资'.

子公司可用于过滤的字段如下：
{keys}

过滤操作operation有如下：
<:小于某值
>:大于某值
contain:包含某值
sum:对于某key进行求和，此时的value为空字符串
top:找出字段key的第几高/大，此时的value为int，比如value是1时表示找出key最高，value是2时表示找出key第二高，依次类推
bottom:找出字段key的倒数第几或者第几小，此时的value为int，比如value是1时表示找出key最小或者说倒数第一，value是2时表示找出key第二小或者倒数第二，依次类推
tops:找出字段key的前几高/大，此时的value为int，比如value是5时表示找出前5高的结果，依次类推
bottoms:找出字段key的前第几低/小，此时的value为int，比如value是5时表示找出前5小的结果，依次类推


请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：中山华利实业集团股份有限公司注册与办公的登记地址是否相同？该公司投资的子公司有多少家？投资总额为多少？
```json
[
    "intersection",
    {{"key":"上市公司投资金额","operation":"sum","value":""}}
]
``` 

example：重庆秦安机电股份有限公司投资金额最高的子公司是？投资金额是？
```json
[   
    "intersection",
    {{"key":"上市公司投资金额","operation":"top","value":1}}
]
``` 

example：天津七一二通信广播股份有限公司投资金额最高的子公司与投资最低的子公司注册地址所在城市分别是？
```json
[
    "union",
    {{"key":"上市公司投资金额","operation":"top","value":1}},
    {{"key":"上市公司投资金额","operation":"bottom","value":1}}
]
``` 

example：代码为300682的公司的子公司是否有涉诉？
```json
[
]
``` 

example：金迪克的子公司的一级行业是什么？
分析：一级行业不在过滤的key中，所以没有任何过滤条件
```json
[
]
``` 

example：中国铁路通信信号股份有限公司投资的圈资公司有哪些？投资金额分别为？
```json
[
    "intersection",
    {{"key":"上市公司参股比例","operation":"contain","value":"100"}}
]
``` 

example：'金堆城钼业股份有限公司投资过亿的全资子公司分别是？
```json
[   
    "intersection",
    {{"key":"上市公司投资金额","operation":">","value":"100000000"}},
    {{"key":"上市公司参股比例","operation":"contain","value":"100"}}
]
``` 

<原始问题>
{query}
</原始问题>

{provided_information}

过滤条件：(不要回答问题)"""

prompt_filter_condition_get_xzgxf_info_list = """对于复杂的统计型问题的解决思路一般分为"根据条件找出潜在答案的数组集合"再"根据问题中的条件对于潜在答案的数组集合进行过滤"这两步。
请根据原始问题、已知信息以及数组元素的key集合，给出对于该数组合计的过滤条件，过滤条件是一个数组，数组元素是键值对，包含key：过滤的键值、operation：过滤操作，value：过滤的值。不要回答问题之外的内容。
只需要找出原始问题中逻辑链(子问题)关于限制高消费数据表相关内容，也就是限制高消费数据表可以给出的字段，返回结果中的key只能从下面的key列表中选择。
除了一些需要过滤的字段，也要考虑某些成为后续问题前提条件的字段，这些字段只有key也就是字段名，operation和value都为空，因为不要过滤。比如'最高涉案金额为多少元？该案件的案号为？'，只对'涉案金额'做了top1过滤，而'案号'不要过滤，它的operation和value都为空。

可选择key的列表如下：
{keys}

过滤操作operation有如下：
<:小于某值
>:大于某值
contain:包含某值
sum:对于某key进行求和，此时的value为空字符串
top:找出字段key的第几高/大，此时的value为int，比如value是1时表示找出key最高，value是2时表示找出key第二高，依次类推
bottom:找出字段key的倒数第几或者第几小，此时的value为int，比如value是1时表示找出key最小或者说倒数第一，value是2时表示找出key第二小或者倒数第二，依次类推
tops:找出字段key的前几高/大，此时的value为int，比如value是5时表示找出前5高的结果，依次类推
bottoms:找出字段key的前第几低/小，此时的value为int，比如value是5时表示找出前5小的结果，依次类推


请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
要区分问题中对于不同字段的过滤条件，比如'最高涉案金额为多少元？该案件的案号为？'，只对'涉案金额'做了top1过滤，而'案号'只是询问该字段具体内容而没有做任何过滤。
example：龙龙元建设集团股份有限公司的法人信息与总经理是否相同？该公司是否被限制高消费了？如果被限制高消费的话，最高涉案金额为多少元？该案件的案号为？调用了多少类API？
已知信息：根据:龙元建设集团股份有限公司,查询到:{{'法人代表': '赖朝辉', '总经理': '赖朝辉'}}
```json
[
    {{"key":"涉案金额","operation":"top","value":1}}，
    {{"key":"案号","operation":"","value":""}}
]
``` 

example：(2019)陕民申98号的被告是否为上市公司，如果是的话，他的股票代码和上市日期分别是？如果不是的话，统一社会信用代码是？该公司是否被限制高消费？如果是被限制高消费的涉案金额总额为？
```json
[   
    {{"key":"涉案金额","operation":"sum","value":""}}
]
``` 

<原始问题>
{query}
</原始问题>

{provided_information}

过滤条件："""

prompt_filter_condition_get_company_info = """对于复杂的问题可以通过逻辑链的方式进行逐步解决，比如通过问题中的某些信息搜索出数据集A，再通过数据集A的某些信息搜索出数据集B，这样一步一步获取最终答案。
在这个场景中已经获取了'上市公司基本信息表'的数据集，请根据原始问题和已知信息返回上市公司基本信息表的字段列表，这个字段列表可以继续执行逻辑链，也就是可以通过这些字段列表的内容搜索出问题中后续内容。

上市公司基本信息表的字段如下：
{keys}

在返回字段列表时要注意除了原始问题直接包含的字段也要考虑一些相近的语义。比如'统一社会信用代码是913310007200456372这家公司的法人是谁',这里'法人'指的是字段'法人代表'
也要联想后续问题搜索条件依赖哪些字段。比如'某公司的子公司是否有涉诉'，后续问题是关于该公司的子公司信息，需要返回字段'公司名称'，因为子公司信息需要通过母公司名称来搜索。
当问到与公司关联的案件审理法院信息,需要返回字段'公司名称'，因为案件需要通过公司名和工具get_legal_document_list获取.

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：龙龙元建设集团股份有限公司的法人信息与总经理是否相同？
```json
{{"key":["法人代表","总经理"]}}
``` 

example：代码为300682的公司的子公司是否有涉诉？
```json
{{"key":["公司名称"]}}
``` 

example：中山华利实业集团股份有限公司注册与办公的登记地址是否相同？
```json
{{"key":["注册地址","办公地址"]}}
``` 
<原始问题>
{query}
</原始问题>

{provided_information}
返回字段列表："""

prompt_filter_condition_get_company_register = """对于复杂的问题可以通过逻辑链的方式进行逐步解决，比如通过问题中的某些信息搜索出数据集A，再通过数据集A的某些信息搜索出数据集B，这样一步一步获取最终答案。
在这个场景中已经获取了'公司工商照面信息表'的数据集，请根据原始问题和已知信息返回公司工商照面信息表的字段列表，这个字段列表可以继续执行逻辑链，也就是可以通过这些字段列表的内容搜索出问题中后续内容。

返回的字段必须从下列字敦列表中选择,对于问题中提到的目标字段需要匹配到下列字段列表，比如'成立时间'须转成下列字段中的'成立日期'不能超出以下字段列表。：
{keys}

在返回字段列表时要注意除了原始问题直接包含的字段也要考虑一些相近的语义。比如'统一社会信用代码是913310007200456372这家公司的法人是谁',这里'法人'指的是字段'法定代表人'

请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题以外的内容，不作任何解释，不输出其他任何信息。
example：玉门拓璞科技开发有限责任公司的地址在哪里？该公司被限告的涉案总额为？总数为？
```json
{{"key":["企业地址"]}}
``` 
<原始问题>
{query}
</原始问题>

{provided_information}
返回字段列表："""

prompt_filter_result = """给定一个List和过滤条件，请用过滤条件对List进行过滤。请直接返回根据条件过滤后的List。不要回答问题之外的内容。

<过滤条件>
{filter_condition}
</过滤条件>

<List>
{list_to_be_processed}
</List>

过滤后的List：(不要回答问题)"""

prompt_final_result = """
请根据已知信息回答问题。所有已知信息可以组成逻辑链，即下一条已知信息的关键信息可以从上一条已知信息中找到。已知信息的格式都是“通过条件A，查询到结果B”，下一条已知信息的条件A可以在上一条已知信息的结果B中找到。
解题思路是把所有已知信息的逻辑链组成一个完整答案，再集合着问题对答案进行修饰。最终答案需要包含所有已知信息中逻辑链的信息，答案可以'啰嗦'但不能遗漏掉任何已知信息中逻辑链信息。
答案中必须包含所有已知信息中的关键信息，不要遗漏任何已知信息。不作任何解释，不输出其他任何信息，不要回答问题之外的内容。
比如原始问题问的是'公司注册地址所在城市',已知信息是:'根据:天津七一二移动通信有限公司和接口:get_company_register,查询到:{{'天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11', '企业地址'}} 根据:天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11和接口:get_address_info,查询到:{{'省份': '天津市', '城市': '天津市', '区县': '滨海新区'}}'.答案必须包含这样的逻辑链：'根据天津七一二移动通信有限公司查询到注册地址是天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11,所在城市是天津市'。
比如已知信息:'根据北京市北京市海淀区查询到:{{"城市区划代码": "110100000000"}}'，那么答案必须包含这样的逻辑链：'根据北京市北京市海淀区查询到城市区划代码是110100000000'。
比如已知"根据烟台市招远市招金路南首皮草小镇烟台路8号查询:{{"区县”: “招远市"}}‘,那么答案必须包含这样的逻辑链：'根据烟台市招远市招金路南首皮草小镇烟台路8号查询到区县是招远市'。
比如已知"根据案号(2019)冀01民终10768号查询到:{{"被告": "石家庄中汇药品包装有限公司"}}",那么答案必须包含这样的逻辑链：'根据案号(2019)冀01民终10768号查询到被告是石家庄中汇药品包装有限公司'。
比如已知"根据:简称天通股份和接口:get_company_info,查询到:公司的全称是安徽安利材料科技股份有限公司",答案必须包含这样的逻辑链：'根据简称天通股份查询到全称是安徽安利材料科技股份有限公司'。

注意如果条件A是法院代字并且是由字段'案号'中获取，那么在答案中需要包含完整的'案号字段以及“由案号***获取法院代字***”这一逻辑链。
如果问题中的案号不标准比如案号的年份没有中括号或者用了其他类型的括号，那么在答案中需要包含"由案号**得到标准格式的案号**"这一逻辑链。比如问题中的案号是'【2021】豫0304民初300号'时，答案中需要包含：由案号【2021】豫0304民初300号得到标准格式的案号(2021)豫0304民初300号
如果问题中询问某些数字字段有哪些，回答时要把数字为0的也加上。比如问涉案金额有哪些，如果有涉案金额为0时答案中需要包含该金额0。
请严格按照给定的已知信息的关键词进行回答，不要进行总结或者改写，哪怕给定的信息项不规范，比如给出'网址'或'通讯邮箱'信息是一个横杠'-'，在答案中也回答网址是-或通讯邮箱是-。非相关信息请不要回答。
对于金额问题最终答案不要使用千分位，金额单位需要和问题一致，比如问题中问总金额多少元，那么回答**元，如果问总金额多少万元，那么答案也要转成**万元。
在最终答案中不要包含<已知信息>中具体API的名。

当问API时需要根据'已知信息'的内容进行分析判断：
'根据案号**查询到法院代字**'算是常识，不能算调用API。
注意区分API个数和最小调用次数。如接口get_court_code调用了1次，get_court_info调用了2次，get_address_info调用了1次，那么API个数为3个,最小调用次数为4次，多少类API等同于API个数所以此处调用了3类API.
API串行是指第二个api参数必须通过前一个api的搜索结果中获得，API串行调用次数比串行的API个数少一个，因为第二个API的参数才开始需要从上一个API结果中获取。比如逻辑链：'根据代字豫0302查询get_court_codeAPI，法院名称为洛阳市老城区人民法院'、'根据法院名称洛阳市老城区人民法院查询get_court_infoAPI，法院地址为洛阳市老城区道德路中段'、'根据法院地址洛阳市老城区道德路中段查询get_addr_infoAPI，法院所在区县为老城区'。本逻辑链涉及API串行调用的次数为2次（get_court_infoAPI及get_addr_infoAPI），串行了3个API（get_court_codeAPI----get_court_infoAPI----get_addr_infoAPI）。
当问题中出现并行逻辑链在问API调用次数或串行次数时需要考虑两条逻辑链调用API的总和。比如以下已知信息：
1. 根据:天津七一二通信广播股份有限公司和接口:get_sub_company_info_list,查询到:天津七一二通信广播股份有限公司的子公司为4家，满足问题要求的子公司有2家，子公司信息如下:[{{'公司名称': '天津七一二移动通信有限公司'}}, {{'公司名称': '北京通广龙电子科技有限公司'}}]
2. 根据:天津七一二移动通信有限公司和接口:get_company_register,查询到:{{'企业地址', '天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11'}}
3. 根据:天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11和接口:get_address_info,查询到:{{'省份': '天津市', '城市': '天津市', '区县': '滨海新区'}}
4. 根据:北京通广龙电子科技有限公司和接口:get_company_register,查询到:{{'企业地址', '北京市海淀区丰慧中路7号新材料创业大厦11层南侧办公1102号、北侧办公1101号'}}
5. 根据:北京市海淀区丰慧中路7号新材料创业大厦11层南侧办公1102号、北侧办公1101号和接口:get_address_info,查询到:{{'省份': '北京市', '城市': '北京市', '区县': '海淀区'}}
这里串行了API类数(也就是去掉重复后串行API个数)是3个:get_sub_company_info_list,get_company_register,get_address_info。串行次数是4次:已知信息2用到已知信息1中的子公司名、已知信息3用到已知信息2中的企业地址、已知信息4用到已知信息1中的子公司名、已知信息5用到已知信息4中的企业地址。
答案要遵循API相关问题格式,需要用问题中相同的量词，比如问'API个数是多少',那么需要回答'API*个'；比如问'API调用次数',那么回答'API调用了*次';比如问'调用API的ci数为？',那么回答'调用API的次数为*次'.

---example：
<问题>
原告是安利股份的案件审理法院是哪家法院
</问题>

<已知信息>
根据:安利股份和接口:get_company_info,查询到:安徽安利材料科技股份有限公司
根据:安徽安利材料科技股份有限公司接口:get_legal_document_list,查询到:安徽安利材料科技股份有限公司的涉案次数为2，满足问题要求的法律文书有1份，法律文书信息如下:['关联公司': '安徽安利材料科技股份有限公司', '标题': '安徽安利材料科技股份有限公司、浙江沃兹科技有限公司买卖合同纠纷执行实施类执行裁定书', '案号': '(2020)皖0123执1262号', '文书类型': '执行裁定书', '原告': '安徽安利材料科技股份有限公司', '被告': '浙江沃兹科技有限公司', '原告律师事务所': '', '被告律师事务所': '', '案由': '买卖合同纠纷', '涉案金额': '0', '判决结果': '终结(2020)皖0123执1262号案件的执行 。  \\n \\n本裁定送达后立即生效 。 ', '日期': '2020-05-29 00:00:00', '文件名': '（2020）皖0123执1262号.txt']
根据法院代字是皖0123查询到法院信息:['法院名称': '肥西县人民法院', '行政级别': '区县级', '法院级别': '基层法院', '法院代字': '皖0123', '区划代码': '340123', '级别': '1']
</已知信息>

答案：经查询，安利股份的公司全称是安徽安利材料科技股份有限公司，原告是安利股份的案件案号为(2020)皖0123执1262号，由案号(2020)皖0123执1262号获取法院代字皖0123，审理法院名称是肥西县人民法院。
---

<问题>
{query}
</问题>

<已知信息>
{information}
</已知信息>

答案："""

prompt_final_result_without_API = """
请根据逻辑链回答问题。即下一条逻辑链的关键信息可以从上一条逻辑链中找到。逻辑链的格式都是“通过条件A，查询到结果B”，下一条逻辑链的条件A可以在上一条逻辑链的结果B中找到。
解题思路是把所有逻辑链组成一个完整答案，再结合原始问题对答案进行修饰。最终答案需要包含所有逻辑链的信息，答案可以'啰嗦'但不能遗漏掉任何逻辑链的信息。
答案中必须包含所有逻辑链中的关键信息，不要遗漏任何逻辑链。不作任何解释，不输出其他任何信息，不要回答问题之外的内容。
比如原始问题问的是'公司注册地址所在城市',逻辑链是:'根据:天津七一二移动通信有限公司和接口:get_company_register,查询到:{{'天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11', '企业地址'}} 根据:天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11和接口:get_address_info,查询到:{{'省份': '天津市', '城市': '天津市', '区县': '滨海新区'}}'.答案必须包含这样的逻辑链：'根据天津七一二移动通信有限公司查询到注册地址是天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11,所在城市是天津市'。
比如逻辑链:'根据北京市北京市海淀区查询到:{{"城市区划代码": "110100000000"}}'，那么答案必须包含这样的逻辑链：'根据北京市北京市海淀区查询到城市区划代码是110100000000'。
比如已知"根据烟台市招远市招金路南首皮草小镇烟台路8号查询:{{"区县”: “招远市"}}‘,那么答案必须包含这样的逻辑链：'根据烟台市招远市招金路南首皮草小镇烟台路8号查询到区县是招远市'。
比如已知"根据案号(2019)冀01民终10768号查询到:{{"被告": "石家庄中汇药品包装有限公司"}}",那么答案必须包含这样的逻辑链：'根据案号(2019)冀01民终10768号查询到被告是石家庄中汇药品包装有限公司'。
比如已知"根据:简称天通股份和接口:get_company_info,查询到:公司的全称是安徽安利材料科技股份有限公司",答案必须包含这样的逻辑链：'根据简称天通股份查询到全称是安徽安利材料科技股份有限公司'。

注意如果条件A是法院代字并且是由字段'案号'中获取，那么在答案中需要包含完整的'案号字段以及“由案号***获取法院代字***”这一逻辑链。
如果问题中的案号不标准比如案号的年份没有中括号或者用了其他类型的括号，那么在答案中需要包含"由案号**得到标准格式的案号**"这一逻辑链。比如问题中的案号是'【2021】豫0304民初300号'时，答案中需要包含：由案号【2021】豫0304民初300号得到标准格式的案号(2021)豫0304民初300号
如果问题中询问某些数字字段有哪些，回答时要把数字为0的也加上。比如问涉案金额有哪些，如果有涉案金额为0时答案中需要包含该金额0。
请严格按照给定的逻辑链的关键词进行回答，不要进行总结或者改写，哪怕给定的信息项不规范，比如给出'网址'或'通讯邮箱'信息是一个横杠'-'，在答案中也回答网址是-或通讯邮箱是-。非相关信息请不要回答。
对于金额问题最终答案不要使用千分位，金额单位需要和问题一致，比如问题中问总金额多少元，那么回答**元，如果问总金额多少万元，那么答案也要转成**万元。
原始问题中规定了保留几位小数,则对应数值按要求保留几位小数.比如计算出总额是173799500.0,题目要求'结果保留3位小数',那么答案应该是:173799500.000。
当问题需要列出案件或限制高消费时,答案要带上案号.
当问'是否被限制高消费/如果被限制高消费',要回答'被限制高消费了'或'没被限制高消费'.
答案中需要带上单位,比如问道温度、湿度时回答:*度.
当问AB两项是否相同时格式如下:A和B相同,都是**；A和B不同,A是**,B是**.
输出的日期格式为XXXX年XX月XX日,几月几日如果是个位数需要在十位上加0，如：应该2020年4月3日变成2020年04月03日。

最终答案要简洁,如果一个实例名称已经出现一次了那么后续答案中可以不用再出现。比如问某法院是什么时候成立的？
可以回答:由案号**，查询到法院名称是**法院，成立日期是2019年05月16日。
而不要回答成：由案号**，查询到法院名称是**法院，**法院成立日期是2019年05月16日。
这里的**法院已经出现过一次那么后面的成立时间前面就不用再出现**法院。

如问'300164的法定代表人及工商电话注册资本是多少亿元？',可以回答:'根据公司代码300164查询到公司名称是通源石油科技集团股份有限公司，法定代表人是**，工商电话是**，注册资本是**'。这里公司名只要出现一次即可.

在最终答案中不要包含<逻辑链>中具体API的名。

---example：
<问题>
原告是安利股份的案件审理法院是哪家法院
</问题>

<逻辑链>
根据:安利股份和接口:get_company_info,查询到:安徽安利材料科技股份有限公司
根据:安徽安利材料科技股份有限公司接口:get_legal_document_list,查询到:安徽安利材料科技股份有限公司的涉案次数为2，满足问题要求的法律文书有1份，法律文书信息如下:['关联公司': '安徽安利材料科技股份有限公司', '标题': '安徽安利材料科技股份有限公司、浙江沃兹科技有限公司买卖合同纠纷执行实施类执行裁定书', '案号': '(2020)皖0123执1262号', '文书类型': '执行裁定书', '原告': '安徽安利材料科技股份有限公司', '被告': '浙江沃兹科技有限公司', '原告律师事务所': '', '被告律师事务所': '', '案由': '买卖合同纠纷', '涉案金额': '0', '判决结果': '终结(2020)皖0123执1262号案件的执行 。  \\n \\n本裁定送达后立即生效 。 ', '日期': '2020-05-29 00:00:00', '文件名': '（2020）皖0123执1262号.txt']
根据法院代字是皖0123查询到法院信息:['法院名称': '肥西县人民法院', '行政级别': '区县级', '法院级别': '基层法院', '法院代字': '皖0123', '区划代码': '340123', '级别': '1']
</逻辑链>

答案：根据安利股份查到公司全称时安徽安利材料科技股份有限公司，原告是安利股份的案件案号为(2020)皖0123执1262号，由案号获取法院代字皖0123，审理法院名称是肥西县人民法院。
---

{prompt_4_API}

<问题>
{query}
</问题>

<逻辑链>
{information}
</逻辑链>

答案："""

prompt_final_result_without_API_report = """
请根据逻辑链回答问题。即下一条逻辑链的关键信息可以从上一条逻辑链中找到。逻辑链的格式都是“通过条件A，查询到结果B”，下一条逻辑链的条件A可以在上一条逻辑链的结果B中找到。
解题思路是把所有逻辑链组成一个完整答案，再结合原始问题对答案进行修饰。最终答案需要包含所有逻辑链的信息，答案可以'啰嗦'但不能遗漏掉任何逻辑链的信息。
答案中必须包含所有逻辑链中的关键信息，不要遗漏任何逻辑链。不作任何解释，不输出其他任何信息，不要回答问题之外的内容。
比如原始问题问的是'公司注册地址所在城市',逻辑链是:'根据:天津七一二移动通信有限公司和接口:get_company_register,查询到:{{'天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11', '企业地址'}} 根据:天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11和接口:get_address_info,查询到:{{'省份': '天津市', '城市': '天津市', '区县': '滨海新区'}}'.答案必须包含这样的逻辑链：'根据天津七一二移动通信有限公司查询到注册地址是天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11,所在城市是天津市'。
比如逻辑链:'根据北京市北京市海淀区查询到:{{"城市区划代码": "110100000000"}}'，那么答案必须包含这样的逻辑链：'根据北京市北京市海淀区查询到城市区划代码是110100000000'。
比如已知"根据烟台市招远市招金路南首皮草小镇烟台路8号查询:{{"区县”: “招远市"}}‘,那么答案必须包含这样的逻辑链：'根据烟台市招远市招金路南首皮草小镇烟台路8号查询到区县是招远市'。
比如已知"根据案号(2019)冀01民终10768号查询到:{{"被告": "石家庄中汇药品包装有限公司"}}",那么答案必须包含这样的逻辑链：'根据案号(2019)冀01民终10768号查询到被告是石家庄中汇药品包装有限公司'。
比如已知"根据:简称天通股份和接口:get_company_info,查询到:公司的全称是安徽安利材料科技股份有限公司",答案必须包含这样的逻辑链：'根据简称天通股份查询到全称是安徽安利材料科技股份有限公司'。

注意：如果'逻辑链'中包含了整合报告，请不要回答整合报告所用到的公司工商信息、子公司信息、裁判文书和限制高消费这4类信息，因为这些信息已经被整合报告所使用。
比如问题：请把我查询龙建路桥股份有限公司的联系电话，以及该公司关于工商信息（不包括公司简介）及投资金额过亿的全资子公司，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书（不需要判决结果）整合报告
逻辑链：整合报告为：Word_龙建路桥股份有限公司_companyregister1_17_subcompanyinfo5_5_legallist9_12_xzgxflist0_0
回答：龙建路桥股份有限公司的联系电话0513-83742079，整合报告为：Word_龙建路桥股份有限公司_companyregister1_17_subcompanyinfo5_5_legallist9_12_xzgxflist0_0.

注意如果条件A是法院代字并且是由字段'案号'中获取，那么在答案中需要包含完整的'案号字段以及“由案号***获取法院代字***”这一逻辑链。
如果问题中的案号不标准比如案号的年份没有中括号或者用了其他类型的括号，那么在答案中需要包含"由案号**得到标准格式的案号**"这一逻辑链。比如问题中的案号是'【2021】豫0304民初300号'时，答案中需要包含：由案号【2021】豫0304民初300号得到标准格式的案号(2021)豫0304民初300号
如果问题中询问某些数字字段有哪些，回答时要把数字为0的也加上。比如问涉案金额有哪些，如果有涉案金额为0时答案中需要包含该金额0。
请严格按照给定的逻辑链的关键词进行回答，不要进行总结或者改写，哪怕给定的信息项不规范，比如给出'网址'或'通讯邮箱'信息是一个横杠'-'，在答案中也回答网址是-或通讯邮箱是-。非相关信息请不要回答。
对于金额问题最终答案不要使用千分位，金额单位需要和问题一致，比如问题中问总金额多少元，那么回答**元，如果问总金额多少万元，那么答案也要转成**万元。
原始问题中规定了保留几位小数,则对应数值按要求保留几位小数.比如计算出总额是173799500.0,题目要求'结果保留3位小数',那么答案应该是:173799500.000。
当问题需要列出案件或限制高消费时,答案要带上案号.
当问'是否被限制高消费/如果被限制高消费',要回答'被限制高消费了'或'没被限制高消费'.
答案中需要带上单位,比如问道温度、湿度时回答:*度.
当问AB两项是否相同时格式如下:A和B相同,都是**；A和B不同,A是**,B是**.
输出的日期格式为XXXX年XX月XX日,几月几日如果是个位数需要在十位上加0，如：应该2020年4月3日变成2020年04月03日。

最终答案要简洁,如果一个实例名称已经出现一次了那么后续答案中可以不用再出现。比如问某法院是什么时候成立的？
可以回答:由案号**，查询到法院名称是**法院，成立日期是2019年05月16日。
而不要回答成：由案号**，查询到法院名称是**法院，**法院成立日期是2019年05月16日。
这里的**法院已经出现过一次那么后面的成立时间前面就不用再出现**法院。

如问'300164的法定代表人及工商电话注册资本是多少亿元？',可以回答:'根据公司代码300164查询到公司名称是通源石油科技集团股份有限公司，法定代表人是**，工商电话是**，注册资本是**'。这里公司名只要出现一次即可.

在最终答案中不要包含<逻辑链>中具体API的名。

---example：
<问题>
广汇能源股份有限公司子公司列表，母公司及子公司的立案时间在2019年涉案金额不为0的裁判文书及限制高消费（不需要判决结果）整合报告。
</问题>

<逻辑链>
整合报告为：Word_广汇能源股份有限公司_companyregister1_18_subcompanyinfo147_5_legallist22_12_xzgxflist5_8
</逻辑链>

答案：广汇能源股份有限公司的整合报告为：Word_广汇能源股份有限公司_companyregister1_18_subcompanyinfo147_5_legallist22_12_xzgxflist5_8
---

---example：
<问题>
原告是安利股份的案件审理法院是哪家法院
</问题>

<逻辑链>
根据:安利股份和接口:get_company_info,查询到:安徽安利材料科技股份有限公司
根据:安徽安利材料科技股份有限公司接口:get_legal_document_list,查询到:安徽安利材料科技股份有限公司的涉案次数为2，满足问题要求的法律文书有1份，法律文书信息如下:['关联公司': '安徽安利材料科技股份有限公司', '标题': '安徽安利材料科技股份有限公司、浙江沃兹科技有限公司买卖合同纠纷执行实施类执行裁定书', '案号': '(2020)皖0123执1262号', '文书类型': '执行裁定书', '原告': '安徽安利材料科技股份有限公司', '被告': '浙江沃兹科技有限公司', '原告律师事务所': '', '被告律师事务所': '', '案由': '买卖合同纠纷', '涉案金额': '0', '判决结果': '终结(2020)皖0123执1262号案件的执行 。  \\n \\n本裁定送达后立即生效 。 ', '日期': '2020-05-29 00:00:00', '文件名': '（2020）皖0123执1262号.txt']
根据法院代字是皖0123查询到法院信息:['法院名称': '肥西县人民法院', '行政级别': '区县级', '法院级别': '基层法院', '法院代字': '皖0123', '区划代码': '340123', '级别': '1']
</逻辑链>

答案：根据安利股份查到公司全称时安徽安利材料科技股份有限公司，原告是安利股份的案件案号为(2020)皖0123执1262号，由案号获取法院代字皖0123，审理法院名称是肥西县人民法院。
---

{prompt_4_API}

<问题>
{query}
</问题>

{information}
答案："""

prompt_4_API = """使用API接口的信息都在'逻辑链'中，'逻辑链'是回答原始问题时调用了哪些API接口获得哪些信息的综合表述。API接口名字都在逻辑链中显示声明。当问到'几类API'时需要过滤掉重复名称的API。
注意区分API个数和最小调用次数。如接口get_court_code调用了1次，get_court_info调用了2次，get_address_info调用了1次，那么API个数为3个,最小调用次数为4次，多少类API等同于API个数所以此处调用了3类API.

API串行是指第二个api参数必须通过前一个api的搜索结果中获得，API'串行次数'比'串行个数'少1个，因为第二个API的参数才开始需要从上一个API结果中获取。
比如逻辑链：'根据代字豫0302和接口:get_court_code，查询到法院名称为洛阳市老城区人民法院'、'根据洛阳市老城区人民法院和接口:get_court_info，查询到法院地址为洛阳市老城区道德路中段'、'根据洛阳市老城区道德路中段和接口:get_addr_info，查询到法院所在区县为老城区'。
本逻辑链中API串行次数为2次（从get_court_code到get_court_info,从get_court_info到get_addr_info），串行了3个API（get_court_code,get_court_info,get_addr_info）。

当问题中出现并行逻辑链在问API调用次数或串行次数时需要考虑两条逻辑链调用API的总和。比如以下逻辑链：
1. 根据:天津七一二通信广播股份有限公司和接口:get_sub_company_info_list,查询到:天津七一二通信广播股份有限公司的子公司为4家，满足问题要求的子公司有2家，子公司信息如下:[{{'公司名称': '天津七一二移动通信有限公司'}}, {{'公司名称': '北京通广龙电子科技有限公司'}}]
2. 根据:天津七一二移动通信有限公司和接口:get_company_register,查询到:{{'企业地址', '天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11'}}
3. 根据:天津经济技术开发区滨海-中关村科技园荣晟广场4号楼1门506-11和接口:get_address_info,查询到:{{'省份': '天津市', '城市': '天津市', '区县': '滨海新区'}}
4. 根据:北京通广龙电子科技有限公司和接口:get_company_register,查询到:{{'企业地址', '北京市海淀区丰慧中路7号新材料创业大厦11层南侧办公1102号、北侧办公1101号'}}
5. 根据:北京市海淀区丰慧中路7号新材料创业大厦11层南侧办公1102号、北侧办公1101号和接口:get_address_info,查询到:{{'省份': '北京市', '城市': '北京市', '区县': '海淀区'}}
这里串行了API类数(也就是去掉重复后串行API个数)是3个:get_sub_company_info_list,get_company_register,get_address_info。串行次数是4次:逻辑链2用到逻辑链1中的子公司名、逻辑链3用到逻辑链2中的企业地址、逻辑链4用到逻辑链1中的子公司名、逻辑链5用到逻辑链4中的企业地址。
答案要遵循API相关问题格式,需要用问题中相同的量词，比如问'API个数是多少',那么需要回答'API*个'；比如问'API调用次数',那么回答'API调用了*次';比如问'调用API的ci数为？',那么回答'调用API的次数为*次'.

API example：山东潍坊润丰化工股份有限公司投资金额最高的子公司与投资最低的子公司注册地址所在城市分别是？串行了几类API？串行了几次？
逻辑链：根据:琼02和接口:get_court_code,查询到:{{'法院名称', '海南省三亚市中级人民法院'}}
根据:海南省三亚市中级人民法院和接口:get_court_info,查询到:{{'法院地址', '三亚市天涯区金鸡岭路383号'}}
根据:三亚市天涯区金鸡岭路383号和接口:get_address_info,查询到:{{'省份': '海南省', '城市': '三亚市', '区县': '天涯区'}}
根据:['海南省', '三亚市', '天涯区']和接口:get_address_code,查询到:{{'省份': '海南省', '城市': '三亚市', '城市区划代码': '460200000000', '区县': '天涯区', '区县区划代码': '460204000000'}}
分析：get_court_info的查询条件从get_court_code的查询结果获取，get_address_info的查询条件从get_court_info的查询结果获取，get_address_code的查询条件从get_address_info的查询结果获取。
这4个API是都是串行API，所以串行个数是4个，这4个API不重复所以串行类别有4类，串行次数比串行个数少一个所以串行了3次。
```答案：
串行了4类API,串行了3次.
``` 

API example：请查询谱尼测试集团股份有限公司这家公司的股票代码统一社会信用代码董事会秘书工商登记的电话分别是什么？本题目最小调用ＡＰＩ的次数为？串行次数为？
逻辑链：根据:通源石油科技集团股份有限公司和接口:get_company_info,查询到:{{'董秘': '张旭', '公司名称': '通源石油科技集团股份有限公司', '公司代码': '300164'}}
根据:通源石油科技集团股份有限公司和接口:get_company_register,查询到:{{'统一社会信用代码': '91610131294266794G', '联系电话': '029-87607460'}}
分析：调用了get_company_info和get_company_register，这两个api参数必都不用从其他api的搜索结果中获取，所以串行次数是0次
```答案：
最小调用ＡＰＩ的次数为2次,串行次数为0次
``` 
"""

tool_names_of_list_result = ["get_legal_document_list"]


def filter_tool_results_by_column(tool_results_return, filter_conditions):
    # column_names = [filter_condition['key'] for filter_condition in filter_conditions if filter_condition['operation'] not in ['top', 'bottom', 'tops', 'bottoms']]
    column_names = [filter_condition["key"] for filter_condition in filter_conditions]
    if column_names:
        filtered_tool_results = []
        for tool_result in tool_results_return:
            item = {}
            for column_name in column_names:
                if column_name in tool_result.keys():
                    item[column_name] = tool_result[column_name]
            filtered_tool_results.append(item)
        return filtered_tool_results
    else:
        return tool_results_return


def filter_tool_results_by_property_list(tool_results_return, property_list):
    properties = property_list.get("key", "")
    if properties:
        filtered_tool_results = []
        for tool_result in tool_results_return:
            item = {}
            for column_name in properties:
                if column_name in tool_result.keys():
                    item[column_name] = tool_result[column_name]
            filtered_tool_results.append(item)
        return filtered_tool_results
    else:
        return tool_results_return


def filter_tool_results_by_conditions(tool_results_return, filter_conditions, exclude_column=True):
    for filter_condition in filter_conditions:
        operation = filter_condition["operation"]
        if operation in ["top", "bottom", "tops", "bottoms"]:
            values = [tool_result.get(filter_condition["key"], "") for tool_result in tool_results_return]

            new_values = []
            for value in values:
                try:
                    value = value.replace("千", "*1e3")
                    value = value.replace("万", "*1e4")
                    value = value.replace("亿", "*1e8")
                    value = eval(value)
                except Exception as e:
                    value = 0
                new_values.append(value)

            keys = list(range(len(new_values)))
            ranked_keys = rank(keys, new_values)
            # re_rank tool_results_return by ranked_keys
            tool_results_return = [tool_results_return[i] for i in ranked_keys]
            if operation == "top":
                tool_results_return = [tool_results_return[0 - filter_condition["value"]]]
            elif operation == "bottom":
                tool_results_return = [tool_results_return[filter_condition["value"] - 1]]
            elif operation == "tops":
                tool_results_return = tool_results_return[0 - filter_condition["value"] :]
            elif operation == "bottoms":
                tool_results_return = tool_results_return[: filter_condition["value"]]

    if exclude_column:
        filtered_tool_results = []
        for tool_result in tool_results_return:
            exclude = False
            for filter_condition in filter_conditions:
                key = filter_condition["key"]
                if key in tool_result.keys():
                    tool_result_value = tool_result[key]
                    operation = filter_condition["operation"]
                    value = filter_condition["value"]
                    if operation == "contain":
                        if not tool_result_value.__contains__(value):
                            exclude = True
                            break
                    elif operation == "!contain":
                        if tool_result_value.__contains__(value):
                            exclude = True
                            break
                    elif operation == "==":
                        if tool_result_value != value:
                            exclude = True
                            break
                    elif operation == "!=":
                        if tool_result_value == value:
                            exclude = True
                            break
                    if operation in ["<", "<=", ">=", ">"]:
                        if tool_result_value == "":
                            exclude = True
                            break
                        tool_result_value_float = tool_result_value.replace("千", "*1e3")
                        tool_result_value_float = tool_result_value_float.replace("百", "*1e2")
                        tool_result_value_float = tool_result_value_float.replace("万", "*1e4")
                        tool_result_value_float = tool_result_value_float.replace("亿", "*1e8")
                        tool_result_value_float = eval(tool_result_value_float)

                        value_float = value.replace("千", "*1e3")
                        value_float = value_float.replace("百", "*1e2")
                        value_float = value_float.replace("万", "*1e4")
                        value_float = value_float.replace("亿", "*1e8")
                        value_float = eval(value_float)
                        if operation == "<":
                            if tool_result_value_float >= value_float:
                                exclude = True
                                break
                        elif operation == "<=":
                            if tool_result_value_float > value_float:
                                exclude = True
                                break
                        elif operation == ">":
                            if tool_result_value_float <= value_float:
                                exclude = True
                                break
                        elif operation == ">=":
                            if tool_result_value_float < value_float:
                                exclude = True
                                break
                    # elif operation == 'sum':
                    #     if value in tool_result[key]:
                    #         item[key] = tool_result[key]
                    # elif operation == 'equal':
                    #     if value == tool_result[key]:
                    #         item[key] = tool_result[key]
            if not exclude:
                filtered_tool_results.append(tool_result)
        return filtered_tool_results
    else:
        return tool_results_return


def get_sum_result(filtered_tool_results, filter_conditions):
    sum_result = ""
    if filtered_tool_results:
        for filter_condition in filter_conditions:
            if filter_condition.get("operation", "") == "sum":
                key = filter_condition["key"]
                sum_list = [
                    tool_result[key] if tool_result[key] != "" else "0" for tool_result in filtered_tool_results
                ]
                sum_list_result = get_sum(sum_list)
                sum_result = key + "的累加结果是:" + str(sum_list_result) + "。"
    else:
        sum_result = "累加结果是:0"
        sum_result = " "
    return sum_result


def build_provided_information(logic_chain):
    provided_information = ""
    if logic_chain:
        for per_logic in logic_chain:
            if type(per_logic) == list and len(per_logic) == 3:
                provided_information = (
                    provided_information + "根据:" + str(per_logic[0]) + ",查询到:" + str(per_logic[2]) + "\n"
                )
            else:
                provided_information = provided_information + str(per_logic) + "\n"
        provided_information = "<已知信息>\n" + provided_information + "</已知信息>\n"
        provided_information = provided_information.strip()
    else:
        provided_information = ""
    return provided_information


def post_process_tool_results(tool_results, tool_name, args, logic_chain, query):
    # if tool_name not in tool_names_of_list_result:

    if tool_name == "get_legal_document_list":
        try:
            if not tool_results.get("refined_answer").__contains__("无法查询"):
                provided_information = build_provided_information(logic_chain)
                keys = get_table_properties("legal_doc")
                prompt = prompt_filter_condition.format(
                    query=query, provided_information=provided_information, keys=keys
                )
                messages = [{"role": "user", "content": prompt}]
                response = call_glm(messages, model="glm-4-0520")
                filter_conditions = parse_json_from_response(response.choices[0].message.content)
                new_filter_conditions = []
                for filter_condition in filter_conditions:
                    if filter_condition["key"] == "案由":
                        filter_condition["value"] == filter_condition["value"].replace("纠纷", "")
                    if (
                        filter_condition["key"] == "被告"
                        and not query.__contains__("被告")
                        and not query.__contains__("被起诉")
                        and not query.__contains__("被限告")
                    ):
                        continue
                    if (
                        filter_condition["key"] == "原告"
                        and not query.__contains__("原告")
                        and not query.__contains__("起诉人")
                        and not query.__contains__("起诉方")
                    ):
                        continue
                    new_filter_conditions.append(filter_condition)
                new_filter_conditions.append({"key": "案号", "operation": "", "value": ""})
                filtered_tool_results = filter_tool_results_by_column(
                    tool_results.get("api_result").get("return", ""), new_filter_conditions
                )
                # filtered_tool_results = tool_results.get('api_result').get('return', '')
                filtered_tool_results = filter_tool_results_by_conditions(filtered_tool_results, new_filter_conditions)
                sum_result = get_sum_result(filtered_tool_results, new_filter_conditions)

                print_log(filtered_tool_results)

                code = args.strip().rstrip("<|observation|>").strip()
                tool_params = json.loads(code)

                refined_answer = "{}的涉案次数为{}次，满足问题要求的法律文书有{}份，{}法律文书信息如下:{}".format(
                    tool_results.get("condition", ""),
                    str(tool_results.get("api_result").get("return_items_count")),
                    str(len(filtered_tool_results)),
                    sum_result,
                    str(filtered_tool_results),
                )
                api_result = {"return_items_count": len(filtered_tool_results), "return": filtered_tool_results}
                result = {
                    "condition": tool_results.get("condition", ""),
                    "api": "get_legal_document_list",
                    "search_result": refined_answer,
                    "refined_answer": refined_answer,
                    "api_result": api_result,
                    "call_api_successfully": True,
                }
        except Exception as e:
            return tool_results, False
            pass
        return result, True
    if tool_name == "get_sub_company_info_list":
        try:
            if not tool_results.get("refined_answer").__contains__("无法查询"):
                provided_information = build_provided_information(logic_chain)
                keys = get_table_properties("sub_company_info")
                prompt = prompt_filter_condition_get_sub_company_info_list.format(
                    query=query, provided_information=provided_information, keys=keys
                )
                messages = [{"role": "user", "content": prompt}]
                response = call_glm(messages, model="glm-4-0520")
                filter_conditions = parse_json_from_response(response.choices[0].message.content)
                if (
                    type(filter_conditions) == list
                    and len(filter_conditions) > 0
                    and filter_conditions[0] == "intersection"
                ):
                    del filter_conditions[0]
                    filtered_tool_results = filter_tool_results_by_conditions(
                        tool_results.get("api_result").get("return", ""), filter_conditions
                    )
                elif (
                    type(filter_conditions) == list and len(filter_conditions) > 0 and filter_conditions[0] == "union"
                ):
                    del filter_conditions[0]
                    filtered_tool_results = []
                    for filter_condition in filter_conditions:
                        filtered_tool_result = filter_tool_results_by_conditions(
                            tool_results.get("api_result").get("return", ""), [filter_condition]
                        )
                        filtered_tool_results.extend(filtered_tool_result)

                sum_result = get_sum_result(filtered_tool_results, filter_conditions)

                print_log(filtered_tool_results)

                code = args.strip().rstrip("<|observation|>").strip()
                tool_params = json.loads(code)

                refined_answer = "{}的子公司有{}家，满足问题要求的子公司有{}家，{}子公司信息如下:{}".format(
                    tool_results.get("condition", ""),
                    str(tool_results.get("api_result").get("return_items_count")),
                    str(len(filtered_tool_results)),
                    sum_result,
                    str(filtered_tool_results),
                )
                api_result = {"return_items_count": len(filtered_tool_results), "return": filtered_tool_results}
        except Exception as e:
            return tool_results, False
            pass

        result = {
            "condition": tool_results.get("condition", ""),
            "api": "get_sub_company_info_list",
            "search_result": refined_answer,
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": True,
        }
        return result, True
    if tool_name == "get_xzgxf_info_list":
        try:
            if not tool_results.get("refined_answer").__contains__("无法查询"):
                provided_information = build_provided_information(logic_chain)
                keys = get_table_properties("XzgxfInfo")
                prompt = prompt_filter_condition_get_xzgxf_info_list.format(
                    query=query, provided_information=provided_information, keys=keys
                )
                messages = [{"role": "user", "content": prompt}]
                response = call_glm(messages, model="glm-4-0520")
                filter_conditions = parse_json_from_response(response.choices[0].message.content)
                filtered_tool_results = filter_tool_results_by_conditions(
                    tool_results.get("api_result").get("return", ""), filter_conditions, False
                )
                sum_result = get_sum_result(filtered_tool_results, filter_conditions)

                print_log(filtered_tool_results)

                code = args.strip().rstrip("<|observation|>").strip()
                tool_params = json.loads(code)

                if len(filter_conditions) == 1 and filter_conditions[0].get("operation", "") == "sum":
                    refined_answer = "{}的限制高消费次数为{}次，{}".format(
                        tool_results.get("condition", ""),
                        str(tool_results.get("api_result").get("return_items_count")),
                        sum_result,
                    )
                else:
                    refined_answer = "{}的限制高消费总次数为{}次，{}满足问题要求的限制高消费的信息如下:{}".format(
                        tool_params.get("company_name", ""),
                        str(tool_results.get("api_result").get("return_items_count")),
                        sum_result,
                        str(filtered_tool_results),
                    )
                api_result = {"return_items_count": len(filtered_tool_results), "return": filtered_tool_results}
        except Exception as e:
            return tool_results, False
            pass

        result = {
            "condition": tool_results.get("condition", ""),
            "api": "get_xzgxf_info_list",
            "search_result": refined_answer,
            "refined_answer": refined_answer,
            "api_result": api_result,
            "call_api_successfully": True,
        }
        return result, True
    elif tool_name == "get_company_info":
        try:
            if (
                not tool_results.get("refined_answer").__contains__("无法根据")
                and len(tool_results.get("search_result")) > 5
            ):
                if logic_chain:
                    provided_information = "\n".join(logic_chain)
                    provided_information = "<已知信息>\n" + provided_information + "\n</已知信息>\n"
                    provided_information = provided_information.strip()
                else:
                    provided_information = ""
                keys = get_table_properties("company_info")
                prompt = prompt_filter_condition_get_company_info.format(
                    query=query, provided_information=provided_information, keys=keys
                )
                messages = [{"role": "user", "content": prompt}]
                response = call_glm(messages, model="glm-4-0520")
                property_list = parse_json_from_response(response.choices[0].message.content)
                if property_list.get("key", ""):
                    if not "公司名称" in property_list.get("key", ""):
                        property_list["key"].append("公司名称")
                filtered_tool_results = filter_tool_results_by_property_list(
                    tool_results.get("api_result").get("return", ""), property_list
                )

                condition_from_last_result = tool_results.get("condition")
                refined_answer = "根据{},查询到上市公司信息:{}".format(
                    condition_from_last_result, filtered_tool_results[0]
                )
                tool_results["refined_answer"] = refined_answer
                tool_results["search_result"] = filtered_tool_results[0]
            if check_whether_containing_weather(query):
                tool_results["refined_answer"] = (
                    tool_results["refined_answer"]
                    + "\n通过公司地址和工具get_address_info找出公司的省份和城市以供查询天气的工具get_temp_info使用。"
                )
        except Exception as e:
            return tool_results, False
        return tool_results, True
    elif tool_name == "get_company_register":
        try:
            if len(tool_results.get("search_result")) > 5:
                # if True:
                search_result = tool_results.get("search_result")
                if not query.__contains__("简介") and not args.__contains__("简介") and search_result:
                    del search_result["企业简介"]
                if not query.__contains__("范围") and not args.__contains__("范围") and search_result:
                    del search_result["经营范围"]
                    # tool_results.get('api_result')['return'] = tool_results_return
                refined_answer = "根据{},查询到公司工商照面信息:{}".format(
                    tool_results.get("condition"), search_result
                )
                tool_results["refined_answer"] = refined_answer
                tool_results["search_result"] = search_result
                if not tool_results.get("refined_answer").__contains__("无法根据"):
                    provided_information = build_provided_information(logic_chain)
                    keys = get_table_properties("company_register")
                    prompt = prompt_filter_condition_get_company_register.format(
                        query=query, provided_information=provided_information, keys=keys
                    )
                    messages = [{"role": "user", "content": prompt}]
                    response = call_glm(messages, model="glm-4-0520")
                    property_list = parse_json_from_response(response.choices[0].message.content)
                    filtered_tool_results = filter_tool_results_by_property_list([search_result], property_list)

                    condition_from_last_result = tool_results.get("condition")

                    refined_answer = "根据{},查询到公司工商照面信息:{}".format(
                        condition_from_last_result, filtered_tool_results[0]
                    )
                    tool_results["refined_answer"] = refined_answer
                    tool_results["search_result"] = filtered_tool_results[0]
            if check_whether_containing_weather(query):
                tool_results["refined_answer"] = (
                    tool_results["refined_answer"]
                    + "\n通过公司地址和工具get_address_info找出公司的省份和城市以供查询天气的工具get_temp_info使用。"
                )
        except Exception as e:
            return tool_results, False
        return tool_results, True
    elif tool_name == "get_legal_document":
        try:
            if len(tool_results.get("search_result")) > 5:
                search_result = tool_results.get("search_result")
                if not query.__contains__("结果") and not args.__contains__("结果") and search_result:
                    del search_result["判决结果"]
                refined_answer = "根据案号{}查询到:{}".format(tool_results.get("condition"), search_result)
                tool_results["refined_answer"] = refined_answer
                tool_results["search_result"] = search_result
        except Exception as e:
            return tool_results, False
        return tool_results, True
    elif tool_name == "get_lawfirm_info":
        try:
            if check_whether_containing_weather(query):
                tool_results["refined_answer"] = (
                    tool_results["refined_answer"]
                    + "\n通过律师事务所地址和工具get_address_info找出律师事务所的省份和城市以供查询天气的工具get_temp_info使用。"
                )
        except Exception as e:
            return tool_results, False
        return tool_results, True
    elif tool_name == "get_court_info":
        try:
            if check_whether_containing_weather(query):
                tool_results["refined_answer"] = (
                    tool_results["refined_answer"]
                    + "\n通过法院地址和工具get_address_info找出法院的省份和城市以供查询天气的工具get_temp_info使用。"
                )
        except Exception as e:
            return tool_results, False
        return tool_results, True

    return tool_results, False


def check_whether_containing_weather(query):
    if query.__contains__("天气") or query.__contains__("温度") or query.__contains__("湿度"):
        return True
    else:
        return False


def check_API(query, response, information):
    if query.__contains__("api") or query.__contains__("API") or query.__contains__("接口"):
        prompt = prompt_4_API.format(query=query, information=information)
        api_message = [{"role": "user", "content": prompt}]
        api_response = call_glm(api_message, model="glm-4-0520")
        response.choices[0].message.content = (
            response.choices[0].message.content + api_response.choices[0].message.content
        )


@register_tool
def get_sum(
    list_to_be_summed: Annotated[list, "需要求和的数组,数组元素类型是float、int或者只包含数字的str，不能是dict", True],
) -> float:
    """
    对数组的元素进行求和。
    在使用本工具时上下文中一般有一个元素是dict的数组，要把需要求和字段的值提取出来组合成数组作为参数传入本方法。
    """
    params = list_to_be_summed
    return http_api_call_original("get_sum", params)


@register_tool
def rank(
    keys: Annotated[list, "需要排序的key数组", True],
    values: Annotated[list, "需要排序的values数组,也就是被用来进行被排序操作的值的数组", True],
) -> float:
    """
    对数组的元素进行排序，由小到大升序。
    values是用来被排序操作的数组，比如求涉案金额最高的被告，那么values是涉案金额的数组
    keys是最终要得出的排序后的字段或者索引，比如求涉案金额最高的被告，那么keys是被告的数组
    """
    params = {"keys": keys, "values": values}
    return http_api_call_original("rank", params)


# @register_tool
# def get_sum(
#         list_to_be_summed: Annotated[str, "需要求和的数组,该数组中的元素类型是dict，dict的某一个key的value需要被求和", True],
#         key_to_be_summed: Annotated[str, "数组元素dict的某一个需要求和的key", True],
# ) -> float:
#     """
#     对数组的元素某个key的value进行求和。当遇到'总额'或者'金额总和'等求和问题时可以使用本方法。
#     """
#     params = list_to_be_summed
#     return http_api_call("get_sum", params)
