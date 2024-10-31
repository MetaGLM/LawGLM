from llm.router_chain import MetaChain
from utils import *
from tools.tool_correction_info import *
from services.all_tools_service_register import *
from tools.tools_untils import *
from tools.tools_register import *
from preprocess import *
from pprint import pprint
import re 
import os 
import json 
import concurrent.futures
from tqdm import tqdm
import jsonlines
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

question_path = "./data/questions/question_c.json"
test_chain = MetaChain(question_path)
all_tools = get_dict_tools()

def match_col(query, correct_times =2): 
    query = query.replace("（","(").replace("）",")").replace("【","(").replace("】",")")
    key_words = test_chain.keywords.invoke(query)['key_words']
    print(key_words)
    if len(key_words) == 0:
        return False, False, query, {}, {}
    with open("./docs/数据库Shema.md",encoding='utf-8') as file :
        schema = file.read()
    temp_dict = {"schema":schema,"query":query, 'keywords':key_words}
    #匹配关键词
    matched_keywords = test_chain.matchCol.invoke(temp_dict)
    print("HI", matched_keywords)

    entity_keywords = find_entity_keywords(matched_keywords)
    print(entity_keywords)
    corrected_entity_keywords = {}

    fail_to_correct = False # 当需要纠错时，如果纠错失败，则标记为True
    is_abb = False # 检查公司简称-->公司全称
    new_question = query 
    for key, value in entity_keywords.items():
        ##检查公司简称-->公司全称
        print( key, value)
        is_abb, abb_to_full = check_company_abbreviation(key, value)
        
        if is_abb:
            corrected_entity_keywords[key] = abb_to_full
            new_question = new_question.replace(key, abb_to_full)
            print("---公司简称----")
            print(key, abb_to_full)
            print(new_question)
        ##检查是否有效
        vaild_res =  check_entity_validty(key, value)
        
        if "已找到" in vaild_res:
            print(vaild_res)
        else:
            error_corrected_keywords = []
            while correct_times > 0:
                correction_dict = {
                    "query": new_question,
                    "keywords":key,
                    "error_corrected_keywords":error_corrected_keywords
                }
                correct_res = test_chain.correction.invoke(correction_dict)
                correct_key = correct_res['correct_keyword']
                correct_question = correct_res['new_query']
                
                if correct_key != "":
                    vaild_res =  check_entity_validty(correct_key, value)
                    correct_times -= 1
                    if correct_times == 0:
                        fail_to_correct = True 
                if "已找到" in vaild_res:
                    corrected_entity_keywords[key] = correct_key
                    new_question = correct_question
                    print(vaild_res)
                    break
                else:
                    error_corrected_keywords.append(correct_key)
                    print("Correct Failed", correct_times)
                    print("已经纠正的{}为关键词:{}".format(key, error_corrected_keywords))
                    
    ### 修改matched_keywords
    new_matched_keywords = {}
    for key, value in matched_keywords.items():
        if key in corrected_entity_keywords:
            new_matched_keywords[corrected_entity_keywords[key]] =  value
        else:
            new_matched_keywords[key] = value

    return  fail_to_correct, is_abb, new_question, new_matched_keywords, corrected_entity_keywords




def invoke_plan(id, k, plan_task_str,  task_list,  intermmediate_save_info = {}, intermmediate_save_paths = {} ,regulator_limit = 3):
    question_save_folder = os.path.join("./cache/", str(id))
    work_finish = False
    if not os.path.exists(question_save_folder):
        os.makedirs(question_save_folder) 

    for keys, item in task_list.items():
        if keys in intermmediate_save_info:
            continue
        print(f"----------- 任务编号{keys} INTERMMEDIAE SAVE INFO-------------: ")  
        tools = item['tools']
        pre_tasks = item['previous_tasks']

        if "get_listed_company_info_service" in tools or "get_company_register_service" in tools :
            tools.append("get_listed_company_info_service")
            tools.append("get_company_register_service")
            tools = list(set(tools))

        sub_tools_info = []
        sub_task_saving_paths = []
        for tool in tools:
            try:
                sub_tools_info.append(all_tools[tool])
            except:
                print(f"工具{tool}不存在")
            tool_save_path = f"{k}_{keys}_{tool}.csv"
            sub_task_saving_path = os.path.join(question_save_folder,  tool_save_path)
            sub_task_saving_paths.append(sub_task_saving_path)
        #无工具调用
        if len(sub_task_saving_paths) == 0:
            tool_save_path = f"{k}_{keys}.csv"
            sub_task_saving_path = os.path.join(question_save_folder,  tool_save_path)
            sub_task_saving_paths.append(sub_task_saving_path)
      
        intermmediate_save_paths[keys] = ",".join(sub_task_saving_paths)
        try:
            pre_tasks_save_paths = [intermmediate_save_paths[pre_task_key] for pre_task_key in pre_tasks]
        except:
            pre_tasks_save_paths = []
        
        similar_coders = test_chain.find_most_similar_coders(item['task_description'], tools)
        question = f"###你的任务:\n###任务编号{keys} \n##问题: {item['task_description']} "
       
        sub_task_description_path = os.path.join(question_save_folder, str(k) + keys +".txt")
        # print(tools_info)
        # print(question)
        # print("="* 30)
        # print(f"任务{keys} 保存路径为{sub_task_saving_paths}")
        # print("="* 30)

        coder_dict = {
            "tools_info":  sub_tools_info,
            "current_task_save_path": ",".join(sub_task_saving_paths),
            "question": question,
            'context': parse_intermmediate_save_info_to_str(intermmediate_save_info),
            "few_shot_examples": parse_content_list_to_string(similar_coders),
            "plan_str": plan_task_str,
            "pre_task_save_path": ",".join(pre_tasks_save_paths)
        }
        test_chain.coder_shots.set_save_folder(sub_task_description_path)
        coder_res = test_chain.coder_shots.invoke(coder_dict)
        code_execution = coder_res[0]
        code_txt = coder_res[1]
       
        correct_times = regulator_limit
        # sub_task_finished = True if  "error" not in code_execution.lower()  or "代码执行错误" in code_execution.lower() else False
        if 'save_all_company_info_to_doc_service' in tools:
            work_finish = True
            sub_task_finished  = True 
            report_path_dict = {"report_path":sub_task_saving_paths[0]}
            return True, {}, report_path_dict
        sub_task_finished = False
        ### Regulator 检查sub task Coder 是否完成任务
        while not sub_task_finished and correct_times > 0:
            regulator_dict = {
                "tools_info": sub_tools_info,
                "question": question,
                'context': parse_intermmediate_save_info_to_str(intermmediate_save_info),
                "code": code_txt,
                "error_info": code_execution,
                "plan_str":plan_task_str
            }
            regulator_res  = test_chain.regulator.invoke(regulator_dict)
            # pprint(regulator_res)
            sub_task_finished = int(regulator_res['judge'].replace("\'","").strip()) >= 60 and "error" not in code_execution.lower()
            suggestion = regulator_res['remark']
            if not sub_task_finished and correct_times > 1:
               
                test_chain.coder_edit_shots.set_save_folder(sub_task_description_path)
                coder_editor_dict = regulator_dict
                coder_editor_dict["current_task_save_path"] =  ",".join(sub_task_saving_paths)
                # coder_editor_dict["plan_str"] = plan_task_str
                coder_editor_dict["suggestion"] = suggestion
                coder_editor_dict["few_shot_examples"] = parse_content_list_to_string(similar_coders)
                coder_editor_dict["pre_task_save_path"] = ",".join(pre_tasks_save_paths)
                coder_res = test_chain.coder_edit_shots.invoke(coder_editor_dict)
                code_execution = coder_res[0]
                code_txt = coder_res[1] 

                if 'save_all_company_info_to_doc_service' in tools:
                    work_finish = True
                    sub_task_finished  = True 
                    report_path_dict = {"report_path":sub_task_saving_paths[0]}
                    return True, {}, report_path_dict
            correct_times -= 1

        if not sub_task_finished:
            # intermmediate_save_info[keys] = f"问题:{question},\n 结果:{code_execution}"
            print("END PLEN")
            break
        else:
            intermmediate_save_info[keys] = f"问题:{item['task_description']},\n 结果:{code_execution}"

    return False, intermmediate_save_info, intermmediate_save_paths


def invoke_question(question_id, question, similar_plans, regulator_limit = 3 ,tools_info = simplied_tool_info):
    plan_dict = {
        "tools_info": tools_info,
        "question": question,
        "few_shot_examples": parse_content_list_to_string(similar_plans)
    }
    referee_id = 1
    print("----------------id: {}----------------".format(question_id))
    ###Referee 循环
    task_list = test_chain.plan_shots_chain.invoke(plan_dict)
    
    # 加入起诉书检查
    for task in task_list.values():
        if 'get_sue_base_info_serivce' in task['tools']:
            return {'sue':123}
        
    print("----------------Initial plan----------------")
    pprint(task_list)
    correct_task_list = task_list
    plan_sub_task_str = [ f"任务编号:{keys}，{item['task_description']}" for keys, item in task_list.items()]
    plan_task_str = "计划解决问题：{}\n 总体计划:\n".format(question) + "\n".join(plan_sub_task_str)
    work_finished, intermmediate_save_info,intermmediate_save_paths = invoke_plan(question_id, referee_id, plan_task_str ,task_list, {},{} ,regulator_limit)
    judge_dict = {
        "tools_info": tools_info,
        "question": question,
        "plan": json.dumps(task_list, ensure_ascii=False),  # 将 task_list 转换为 JSON 字符串
        "intermediate_results": parse_intermmediate_save_info_to_str(intermmediate_save_info)
    }
    judge_result = test_chain.judge_chain.invoke(judge_dict)
    last_intermmediate_save_info = {}
    if work_finished:
        return intermmediate_save_paths

    # print(judge_result['judge'])
    # print(judge_result['error_steps'])
    # print(judge_result['remark'])
    error_steps = judge_result["error_steps"]
    extra_suggestion = judge_result["remark"] 
    while int(judge_result["judge"]) < 75 and referee_id < 4:
        referee_id += 1
        judge_success = True 
        if error_steps.lower() == "none":
            error_sub_tasks = []
        elif error_steps.lower() == "":     
            judge_success = False # 如果 error_steps 为空字符串，则认为全部错误步骤
            intermmediate_save_info = last_intermmediate_save_info
        else:
            if "," in error_steps:
                error_sub_tasks = [x.strip() for x in error_steps.split(",")]
            else:
                error_sub_tasks = [error_steps.strip()]

        ### 更新有效的中间结果 
        if  judge_success and len(error_sub_tasks) > 0:
            temp_dict = {}
            temp_task_list = {}
            temp_save_paths = {}

            for key, items in intermmediate_save_info.items():
                try:
                    if key not in error_sub_tasks or key in last_intermmediate_save_info.keys():
                        temp_task_list = task_list[key]
                        temp_dict[key] = items
                        temp_save_paths[key] =  intermmediate_save_paths[key]    
                except:
                    pass
            intermmediate_save_info = temp_dict
            correct_task_list = temp_task_list
            last_intermmediate_save_info = intermmediate_save_info
            intermmediate_save_paths = temp_save_paths
            
        plan_dict['last_plan'] = json.dumps(task_list, ensure_ascii=False)
        plan_dict['require_fixed_plan'] = json.dumps(correct_task_list, ensure_ascii=False)
        plan_dict['context_res'] = parse_intermmediate_save_info_to_str(intermmediate_save_info)
        plan_dict['judge_opinion'] = extra_suggestion
        task_list = test_chain.plan_edit_shots_chain.invoke(plan_dict)
        plan_sub_task_str = [ f"任务编号:{keys}，{item['task_description']}" for keys, item in task_list.items()]
        plan_task_str = "计划解决问题：{}\n 总体计划:\n".format(question) + "\n".join(plan_sub_task_str)

        work_finished, intermmediate_save_info,intermmediate_save_paths = invoke_plan(question_id, referee_id,plan_task_str, task_list, intermmediate_save_info,intermmediate_save_paths,regulator_limit)
        
        judge_dict = {
            "tools_info": tools_info,
            "question": question,
            "plan": json.dumps(task_list, ensure_ascii=False),  # 将 task_list 转换为 JSON 字符串
            "intermediate_results": parse_intermmediate_save_info_to_str(intermmediate_save_info)
        }
        judge_result = test_chain.judge_chain.invoke(judge_dict)
        
        # print(judge_result['judge'])
        # print(judge_result['error_steps'])
        # print(judge_result['remark'])
        extra_suggestion = judge_result["remark"] 
        error_steps = judge_result["error_steps"]
        if int(judge_result["judge"]) >= 80:
            break
         
    return intermmediate_save_info



def answer(question_id, question):
    print("问题编号{}, 问题内容{}".format(question_id, question))
    # if "整合" in question or "民事起诉状" in question:
    #     return "抱歉，我无法回答这个问题。"
    fail_to_correct, is_abb, new_question, matched_keywords, corrected_entity_keywords = match_col(question)
    question_with_keywords = new_question 

    schema_list , col_list = parse_matched_keywords(matched_keywords)
    similar_plans = test_chain.find_most_similar_plans(question_with_keywords, schema_list)
    plan_res = invoke_question(question_id, question_with_keywords, similar_plans,3)
    if 'sue' in plan_res.keys():
        import traceback
        import warnings
        warnings.filterwarnings("ignore")

        try:
            # 从问题提取基础信息
            base_info = get_sue_base_info_serivce(question)
            final_edited_sue_info = get_sue_serivce(sue_info = base_info)
            # print(f"详细信息：{final_edited_sue_info}")
            
            return final_edited_sue_info
        except Exception as e:
            error_message = traceback.format_exc()
            print("代码执行错误\n" + error_message)
            
        return None
    elif 'report_path' in plan_res.keys():
        try:
            report_path = plan_res['report_path']
            df = pd.read_csv(report_path)
            return df['整合报告信息'][0].strip("\"")
        except:
            return ""
    else:
        try:
            csv_content = parse_task_list_csv_to_str(plan_res)
        except:
            csv_content = ""
        answer_process = f"更正信息为{corrected_entity_keywords}\n 回答流程如下:{plan_res}"
        summary_dict = {
            "question": question,
            "answer_process": answer_process,
            'csv_contents': csv_content
        }
        summary = test_chain.summary_chain.invoke(summary_dict)
        summary = postprocess_summary(question, summary.content)
        return summary  


def process_query(query):
    # 你的代码逻辑
    try:
        response = answer(int(query["id"]), query["question"])
        if not isinstance(response, str):
            response = str(response)
        content = {
            "id": query["id"],
            "question": query["question"],
            "answer": response
        }
        return content
    except Exception as e:
        content = {
            "id": query["id"],
            "question": query["question"],
            "answer": "Error: " + str(e)
        }
        return content

def worker(query):
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            result = process_query(query)
            return result
        except Exception as e:
            retry_count += 1
            print(f"错误，正在重试第 {retry_count} 次: {e}")
    
    return {
        "id": query["id"],
        "question": query["question"],
        "answer": "Error: Failed after 3 retries"
    }

if __name__ == '__main__':
    question_file = "./tcdata/question_c.json"
    result_file = "./result_cashe.json"
    queries = read_jsonl(question_file)

    with ProcessPoolExecutor(max_workers=15) as executor, jsonlines.open(result_file, "a") as json_file:
        futures = {executor.submit(worker, query): query for query in queries}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            query = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "id": query["id"],
                    "question": query["question"],
                    "answer": "Error: " + str(exc)
                }
            json_file.write(result)
    
    # 读取文件并逐行解析JSON对象
    with open('./result_cashe.json', 'r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]

    # 根据"id"字段排序
    sorted_data = sorted(data, key=lambda x: x['id'])

    # 将排序后的数据写入新文件，每行一个JSON对象
    with open('./result.json', 'w', encoding='utf-8') as file:
        for item in sorted_data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

    print("排序完成，结果保存在result.json文件中。")