from langchain_openai import ChatOpenAI
from zhipuai import ZhipuAI
import json
import logging
import time


api_key = "6b91e9144289ecd7939ad6c7382e758d.PGrPAwI3SfhllE3d"
glm = ChatOpenAI(
    temperature=0.1,
    # model="glm-4",
    model="glm-4-air",
    # model = 'glm-4',
    openai_api_key=api_key,
    openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
)


client = ZhipuAI(api_key=api_key)


def call_embedding(str_list):

    response = client.embeddings.create(
        model="embedding-2", #填写需要调用的模型编码
        input=str_list
    )
    print(response)
    return response.data

def call_glm4(prompt):
    from langchain_openai import ChatOpenAI
    glm = ChatOpenAI(
        temperature=0.1,
        model="glm-4",
        # model="glm-4-air",
        openai_api_key=api_key,
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/"
    )
    
    try:
        response = glm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error calling GLM-4: {e}")
        return None