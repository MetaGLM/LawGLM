from zhipuai import ZhipuAI
from match_tools.schema import database_schema
from config import *


client = ZhipuAI()

system_prompt = (
    """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。
所提供的工具接口可以查询四张数据表的信息，数据表的schema如下:
"""
    + database_schema
)

web_search_tool = {"type": "web_search", "web_search": {"enable": False}}


def call_glm(
    messages, model="glm-4-plus", temperature=0.1, top_p=0.5, tools=[web_search_tool], max_tokens=1024, do_sample=True
):
    response = client.chat.completions.create(
        model=model,  # 填写需要调用的模型名称
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        tools=tools,
        max_tokens=max_tokens,
    )
    # print_log(messages)
    print_log(response.json())
    return response
