from llm.router_chain import MetaChain 
import jsonlines
from tqdm import tqdm
from utils import read_jsonl
import json
from services.all_tools_service_register import *
from tools.tools_register import * 
log_path = 'log07_10.log'
test_chain = MetaChain(log_path)
tools_info = simplify_tool_desc()
def save_log(log):
    with open(log_path, 'a', encoding='utf-8') as f:
        # print(log)
        f.write(log)
        f.close() 
        
save_log(tools_info)  

def match_col(query): 
    key_words = test_chain.keywords.invoke(query)['key_words']
    # print(key_words)
    search_str = "问题:" + query + "关键词:" + ", ".join(key_words)
    relative_schema = test_chain.schema_retriever.invoke(search_str)
    relative_apis = test_chain.apis_retriever.invoke(search_str)
    temp_dict = {"schema": relative_schema, "api": relative_apis, "query":search_str}
    matched_keywords = test_chain.matchCol.invoke(temp_dict)
    return matched_keywords

def answer(query):
    #matched_col = match_col(query)
    #search_str1 = "问题:" + query + "\n可能涉及到的字段" + str(matched_col)
    search_str1 = query
    save_log(search_str1)
    planing_dict = {
        "tools_info": tools_info,
        "question": search_str1
    }
    planing_res = test_chain.plan_chain.invoke(planing_dict)
    plan = planing_res['plan']
    plan_tools = planing_res['tools']
    tools_search = test_chain.apis_retriever.invoke_for_tools(search_str1,plan_tools)
    search_str2 =  search_str1  + "### 解决问题计划如下：\n" + plan
    test_chain.build_auto_agent(tools=tools_search)
    save_log(search_str2)
    daialog = test_chain.auto_tool_agent.invoke(search_str2)
    daialog_dict = {"daialog": daialog}
    summary_res = test_chain.summary_chain.invoke(daialog_dict)    
    return summary_res.content 

def convert_amounts(answer):
    import re
    
    # 正则表达式匹配金额
    pattern = re.compile(r'(\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?)元')
    matches = pattern.findall(answer)
    
    for match in matches:
        amount_str = match[0].replace(',', '')  # 去掉逗号
        amount = float(amount_str)
        in_wan = amount / 10000
        in_yi = amount / 100000000
        conversion_text = f"{amount}元（{in_wan:.4f}万元，{in_yi:.8f}亿元）"
        answer = answer.replace(match[0]+"元", conversion_text)
    
    return answer
      
         

if __name__ == '__main__':
    question_file = "./data/results/public24点燃心海_result_0710_new.json"
    # 修改输出文件
    result_file = "./data/results/process_new.json"
    queries = read_jsonl(question_file)
    for query in queries:
        query["answer"] = convert_amounts(query["answer"])
        content = {
                "id": query["id"],
                "question": query["question"],  
                "answer": query["answer"]
            }
        with jsonlines.open(result_file, "a") as json_file:
            json_file.write(content)