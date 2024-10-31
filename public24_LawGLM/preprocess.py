from tools.tool_correction_info import *
from tools.tools_untils import *
from services.all_tools_service_register import *
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

def print_plan(plan_dict):
    for keys, item in plan_dict.items():
        print(keys)
        print(item['task_description'])
        print(item['tools'])

def parse_intermmediate_save_info_to_str(intermmediate_save_info):
    res = ""
    for keys, item in intermmediate_save_info.items():
        res += "任务编号: "
        res += keys + " : \n" + item + "\n"
    if res == "":
        res = "无中间结果"
    return res

def find_entity_keywords(matched_keywords):
    entity_keywords = {}
    for key , item in matched_keywords.items():
        ###筛除不必要的无效字段
        print("key",key)
        if key in DEFAULT_UNUSEFUL_INFO:
            continue
        entity_keywords[key] = item

    return entity_keywords

def check_entity_validty(entity, matched_cols):
    matched_cols_str = matched_cols
    print(matched_cols_str)
    ###1.检查公司名称是否在数据库中
    res = ""
    if "公司代码" not in matched_cols_str and ("公司" in matched_cols_str or "限制高消费企业名称" in matched_cols_str) :
        res = find_company_info(entity)
    elif "事务所" in matched_cols_str:
        res = find_lawfirm_info(entity)
    elif "法院" in matched_cols_str:
        res = find_court_info(entity)
    elif "代码" in matched_cols_str or re.search(r'^\d{6,}$', entity) or re.search(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{5,}$', entity):
        res = find_code_info(entity)
    elif "案号" in matched_cols_str or  ")" in entity:
        res = find_reference_info(entity)
    else:
        res = f"{entity}已找到"
    return res 


def parse_shot_data(data):
    plan_dict = {}
    coder_list = []
    temp_coder = {}
    plan_start = False 
    coder_start = False
    content_str = "" 
    for line in data:
        line = line.strip("\n")
        line = line.replace("：", ":")
        line = line.replace("，", ",")
        if "###" in line or line == "":
            continue
        elif "PLAN" in line:
            plan_start = True
 
            continue
        elif "coder" in line.lower():
            if coder_start == True:
                temp_coder['content'] = content_str

                if 'cols' not in temp_coder:
                    temp_coder['cols'] = []
                    print("Not find cols",data[:6])
                if "tools" not in temp_coder:
                    temp_coder['tools'] = []
                coder_list.append(temp_coder)
                temp_coder = {}
                content_str = ""
            coder_start = True
            continue
        elif "问题:" in line:
            line = line.strip("问题:").strip()
            if plan_start == True:
                plan_dict['question'] = line
            elif coder_start == True:
                temp_coder['question'] = line
            continue
        elif "大表:" in  line:
            line = line.strip("大表:").strip()
            
            schema_list = [i.strip() for i in line.split(",")]
            plan_dict['schema_list']  = schema_list
            continue
        elif "调用工具:" in line:
            line = line.strip("调用工具:").strip()
            tool_list = [i.strip() for i in line.split(",")]
            temp_coder['tools'] = tool_list
            continue    
        elif "字段:" in line:
            line = line.strip("字段:").strip()
            col_list = [i.strip() for i in line.split(",")]
            if plan_start:
                plan_dict['cols'] = col_list
            elif coder_start:
                temp_coder['cols'] = col_list
            continue
        elif "}}" == line:
            # print("END PLAN")
            content_str += line 
            plan_dict['content'] = content_str
            content_str = ""
            plan_start = False
            continue
        
        elif "任务保存路径:" in line:
            temp_coder['save_path'] = line.strip("任务保存路径:").strip()
            continue
        elif "前置任务保存路径:" in line:
            temp_coder['pre_task_save_path'] = line.strip("前置任务保存路径:").strip()
            continue

        if plan_start:
            content_str += line + "\n"
        if coder_start:
            content_str += line + "\n"
       

    if coder_start:
        if 'cols' not in temp_coder:
            temp_coder['cols'] = []
            print("Not find cols",data[:6])

        temp_coder['content'] = content_str
        coder_list.append(temp_coder)

    return plan_dict, coder_list

def check_company_abbreviation(entity, matched_cols):
    matched_cols_str = matched_cols
    # print(entity, matched_cols_str)
    if "公司" in matched_cols_str or "限制高消费企业名称" in matched_cols_str:
        try:
            res = get_company_info_service_by_abbreviation(entity.strip("公司"))
            if res.shape[0] != 0:
                return True, res['公司名称'][0]
        except:
            pass 
    return False, entity 

def parse_matched_keywords(matched_keywords):
    ###将matched_keywords解析为大表和字段名称 
    schema_list = []
    col_list = []
    for key, value in matched_keywords.items():
        for v in value:
            try:
                schema = v.split(".")[0]
                col = v.split(".")[1]
                schema_list.append(schema)
                col_list.append(col)
            except:
                continue 
    return list(set(schema_list)), list(set(col_list)) 



def calculate_similarity(target_list, plan_list):
    target_count = Counter(target_list)
    plan_count = Counter(plan_list)
    all_elements = list(set(target_list + plan_list))
    target_vector = [target_count[element] for element in all_elements]
    plan_vector = [plan_count[element] for element in all_elements]

    # 计算余弦相似度
    cos_sim = cosine_similarity([target_vector], [plan_vector])[0][0]
    
    # 添加长度惩罚
    length_penalty = 1 / (1 + 0.1 * abs(len(target_list) - len(plan_list)))
    
    return cos_sim * length_penalty

def find_most_similar_plans(plan_list, schema_list, col_list, k=3):
    # 计算相似度

    similarities = []
    for plan in plan_list:
        schema_similarity = calculate_similarity(schema_list, plan['schema_list'])
        col_similarity = calculate_similarity(col_list, plan['cols'])
        similarities.append((schema_similarity, col_similarity, plan))

    # 按照schema相似度和col相似度排序
    similarities.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # 获取前k个最相似的plans
    most_similar_plans = [item[2] for item in similarities[:k]]

    return most_similar_plans


def find_most_similar_coders(coder_list, tool_list, question, k=3):
    # 计算相似度
    def caluculate_similarity_with_question(question, coder):
            cols = coder['cols']
            total_len = len(cols)
            contain_times = 0
            for col in cols:
                if col in question:
                    contain_times += 1
            return contain_times / total_len

    similarities = []
    for coder in coder_list:
        
        tool_similarity = calculate_similarity(tool_list, coder['tools'])
        question_similarity = caluculate_similarity_with_question(question, coder)
        similarities.append((tool_similarity, question_similarity, coder))

    # 按照schema相似度和col相似度排序
    similarities.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # 获取前k个最相似的plans
    most_similar_plans = [item[2] for item in similarities[:k]]

    return most_similar_plans


def parse_content_list_to_string(content_list):
    str_list = []
    for k, content in enumerate(content_list):
        content_str = f"例子{k+1}:\n"
        if "save_path" in content.keys():
            content_str += "###前置任务保存路径:" + content.get("pre_task_save_path", "无") + "\n"
            content_str += "###任务保存路径:" + content.get("save_path", "无") + "\n"
            content_str += "###问题:" + content.get("question", "无") + "\n"
            content_str += "```python\n" + content.get("content", "无") + "\n" + "```"
        else:
            content_str += "###问题:" + content.get("question", "无") + "\n"
            content_str += "```python\n" + content.get("content", "无") + "\n" + "```"
        str_list.append(content_str)

    return "\n".join(str_list[::-1])