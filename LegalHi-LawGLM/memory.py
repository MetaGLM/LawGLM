import json

memory_path = "./memory.json"
memory_file = open(memory_path, "r")
memory_dict = json.load(memory_file)

query_list = ""
for key in memory_dict.keys():
    query = memory_dict[key]["question"]
    query_list += str(key) + ". " + query + "\n"


MEMORY_PROMPT = """
你是一个高级排序器代理。
请从给定的候选查询列表中精心挑选出与当前问题最为相似、问题中含有的关键元素最类似、解决路径最为吻合的前四个查询，随后，按照相似度从高到低的顺序，将这些查询的问题序号以列表形式清晰排列。确保最贴近的查询位于列表的顶部。

问题：{question}

候选列表：
{query_list}

例子：
问题：伊吾广汇矿业有限公司作为被告的案件中涉案金额小于100万大于1万的案号分别为？涉案金额数值为？
{{
    "相关问题":[1,15,4,5] 
}}

问题：在2019年，江苏省高级人民法院审理的案号为民申6268号的案件中，判决的胜诉方是哪家公司？胜诉方的律师事务所地址位于何处？
{{
    "相关问题":[25,12,14,15] 
}}
例子结束

问题：{question}
请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题，不作任何解释，不输出其他任何信息。
```json
{{
    "相关问题": 
}}
``` 
"""


MEMORY_Refine_PROMPT = """
你是一个擅长反思的高级排序器。
请从下列候选查询列表中审慎挑选出三个与当前问题最为贴近、解决策略最为相似、问题中含有的关键元素最类似且最有可能助力问题高效解决的查询。随后，按照相似度的递增顺序，将这些查询的问题序号以清晰有序的列表形式呈现出来，确保最相关的查询占据列表的前端位置。

问题：{question}

候选列表：
{query_list}

例子：
问题：伊吾广汇矿业有限公司作为被告的案件中涉案金额小于100万大于1万的案号分别为？涉案金额数值为？
{{
    "相关问题":[1,15,4] 
}}

问题：在2019年，江苏省高级人民法院审理的案号为民申6268号的案件中，判决的胜诉方是哪家公司？胜诉方的律师事务所地址位于何处？
{{
    "相关问题":[25,12,14] 
}}
例子结束

问题：{question}
请按照以下json格式进行输出，可以被Python json.loads函数解析。不回答问题，不作任何解释，不输出其他任何信息。
```json
{{
    "相关问题": 
}}
``` 
"""


def get_memory(Memory_list):
    memory = ""
    for memory_id in Memory_list:
        one_query = memory_dict[str(memory_id)]["question"]
        one_solution = memory_dict[str(memory_id)]["solution"]
        memory += "问题: " + one_query + "\n" + one_solution + "\n\n"
    return memory
