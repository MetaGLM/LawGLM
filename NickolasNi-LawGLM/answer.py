import json
import jsonlines
from tqdm import tqdm
from config import *
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue


from match_tools.company_info_tools import *
from match_tools.company_register_tools import *
from match_tools.sub_company_info_tools import *
from match_tools.legal_document_tools import *
from match_tools.court_info_tools import *
from match_tools.court_code_tools import *
from match_tools.law_firm_log_tools import *
from match_tools.law_firm_info_tools import *
from match_tools.address_info_tools import *
from match_tools.address_code_tools import *
from match_tools.temperature_info_tools import *
from match_tools.legal_abstract_tools import *
from match_tools.xzgxf_tools import *
from match_tools.post_process import *
from match_tools.report_tools import *


from match_tools.tools_register import get_tools, dispatch_tool
from match_tools.post_process import post_process_tool_results, prompt_final_result_without_API, prompt_4_API
from match_tools.pre_process import pre_process_company_tools, check_tool_and_args
from match_tools.schema import database_schema
from model import call_glm
from route import get_related_tables, route_tools, predict_direct_or_tools, enhance_tables
import utils
from utils import *
from match_tools.schema import get_schema_prompt
from prompts import system_sue_prompt, suggested_logic_chain_prompt
from answer_report import run_report
from answer_sue import run_sue
from config import isLocal
import answer_report


system_prompt = """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。问题比较复杂需要通过逻辑链的方式逐步获取信息解决问题，即:分析问题用什么接口获取,该接口需要什么参数,该参数又要用什么接口获取，这样一步一步往上追溯。

字段‘法院代字’可以通过字段‘案号’获取,字段‘案号’通常由年份、法院代字和案件序号三部分组成，年份用()括起来，如果问题中年份没有()请加上()变成标准的案号格式。如：(2020)赣0781民初1260号中法院代字是赣0781案件序号是民初1260号、(2019)川01民终12104号中法院代字是川01案件序号是民终12104号。
法院信息可以通过以下逻辑链获取：从‘案号’获取‘法院代字’，用‘法院代字’通过工具get_court_code获取‘法院名称’，用‘法院名称’通过工具get_court_info获取法院基础信息表（名录）CourtInfo。一般审理信息可以从法院信息获取，比如询问审理地址可以回答法院地址。
问题中涉及到的实体名称可能有噪音，法院名称一般格式是*省*市*区*法院。噪音包含但不限于：重复的叠字、法院名字中缺少'省市区'、律师事务所名称不完整。如"龙龙元建设集团股份有限公司"去噪变成"龙元建设集团股份有限公司"，如公司代码"330000116644"去噪变成"300164"，"信息产业电子第十一设计研究院科技工工程程股股份份有有限限公公司司"去噪变成"信息产业电子第十一设计研究院科技工程股份有限公司"，如"北京丰台区人民法院"去噪变成"北京市丰台区人民法院"，"福建漳州中级人民法院"去噪变成"福建省漳州市中级人民法院"，"河南良承事务所"去噪变成"河南良承律师事务所"，"(2020)苏01民民终终1783号"去噪变成"(2020)苏01民终1783号"
天气信息的逻辑链需要日期,省份,城市三者组合。案件信息中包含了日期信息，也包含了律师事务所,公司信息,法院代字，省份,城市信息需要用详细地址和get_address_info工具获取，而详细地址一般是指公司地址、法院地址或律师事务所地址，分别需要通过公司名称和get_company_info获取公司地址、律所名称和get_lawfirm_info获取律所地址、法院名称和get_court_info获取法院地址，而法院名称可以通过法院代字和get_court_code获取。
当问'审理当天的天气'时需要通过案号和get_legal_document获取'日期',因为天气工具get_temp_info包含参数:'日期'.
当用户询问省份、城市、区县时必须通过地址信息和工具get_address_info获取,不能直接从详细地址、名称或者大模型内部信息中获取,必须通过给出的工具查询。当问天气和两地省市是否一致时都需要通过这样逻辑链进行查询。
当问法院的区县,城市或省份时，需要通过法院地址和get_address_info获取法院区县信息,如果没有法院地址需要先通过法院名称和get_court_info获取法院地址,如果没有法院名需要先通过'法院代字'和get_court_code获取法院名称。
当原本是公司名称的位置出现一串数字或者数字和字母组合，比如'原告是300077','91320722MA27RF9U87这家公司'、'91310114312234914L对应的公司'、'代码为300682的公司'，6位纯数字组成的是公司代码，18位数字和字母组成的是统一社会信用代码。此时的逻辑链是：如果是使用工具get_company_register_name和统一社会信用代码查找公司名称，再用工具get_company_info和公司名称查找公司信息，或者用工具get_company_info和公司代码查找公司信息。
查询子公司信息时可以通过母公司名和工具get_sub_company_info_list获取该公司的所有子公司信息。
当问题中要查询的信息在工具get_company_info和get_company_register都有时，必须先调用get_company_info。
当问到公司的两个属性分别在上市公司基本信息表和工商照面信息表时需要调用工具get_company_info和get_company_register查到所有属性,如问公司的统一社会代码和上市日期。
法人信息要通过公司名称和工具get_company_info获取字段'法人代表'
公司的注册地址可以通过公司名称和工具get_company_register获取字段'企业地址'
如果问题中涉及错别字等错误需要先修复。比如'玉门拓璞科技开发有限责任公司的地址在哪里？该公司被限告的涉案总额为？'其中的'被限告'应该改为'被限高'也就是限制高消费
当问一家公司的母公司信息时需要先根据该公司的名字和get_sub_company_info找到其母公司的名字后再通过其母公司名字找到母公司相关信息。
问题中有可能包含拼音,请把拼音转成中文再进行作答.如gongsi,zigongsi,anhao,fayuan,lvshishiwusuo,tianqi,xianzhigaoxiaofei分别代表了公司,子公司,案号,法院,律师事务所,天气和限制高消费

所提供的工具接口可以查询数据表的schema如下:
"""


def get_suggested_logic_chain(query):
    try:
        prompt = suggested_logic_chain_prompt.format(query=query)
        messages = [{"role": "user", "content": prompt}]
        response = call_glm(messages, model="glm-4-0520")
        content = response.choices[0].message.content
        return content
    except Exception as e:
        print_log(e)
        return None


def run(query, tools, related_tables, update_message=True, suggested_logic_chain=False):
    retry_index = 0
    while retry_index < 1:
        print_log(f"------------##retry_index:{retry_index}##------------")
        retry_index = retry_index + 1
        tokens_count = 0

        if suggested_logic_chain:
            logic_chain_str = get_suggested_logic_chain(query)
            user_query = query + "\n可以参考以下逻辑链：\n" + logic_chain_str
        else:
            user_query = query

        sys_prompt = system_prompt + get_schema_prompt(related_tables)
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_query}]

        logic_chain = []
        must_contained_info = set()
        for i in range(10):
            print_log(f"##第{i}轮对话##")
            pprint_log(messages)
            print_log("#" * 10)
            print_log("\n")

            for _ in range(3):
                try:
                    response = call_glm(messages, model="glm-4-plus", tools=tools, temperature=0.11, top_p=0.11)
                    # message, response = parse_content_2_function_call(response.choices[0].message.content, response)
                    message = response.choices[0].message.model_dump()
                    tokens_count += response.usage.total_tokens
                    messages.append(message)
                    break
                except Exception as e:
                    print_log(e)

            try:
                if response.choices[0].finish_reason == "tool_calls":
                    tool_name = message["tool_calls"][0]["function"]["name"]
                    args = message["tool_calls"][0]["function"]["arguments"]
                    args = utils.check_company_name(tool_name, args, logic_chain, must_contained_info)
                    args, tool_name = check_area_4_temperature(tool_name, args, logic_chain, message)
                    if isinstance(args, dict):
                        args = json.dumps(args, ensure_ascii=False)
                    tool_id = message["tool_calls"][0]["id"]

                    tool_name, args = check_tool_and_args(tool_name, args, message, logic_chain, query)

                    obs = dispatch_tool(tool_name, args, "007")
                    if obs.get("call_api_successfully", False):
                        obs, need_tools_4_data_process = post_process_tool_results(
                            obs, tool_name, args, logic_chain, query
                        )
                        if obs.get("condition", ""):
                            if type(obs.get("condition", "")) == list:
                                for condition in obs.get("condition", ""):
                                    must_contained_info.add(condition)
                            else:
                                must_contained_info.add(obs.get("condition", ""))
                        # if need_tools_4_data_process:
                        #     tools.extend([all_tools.get('get_sum')])

                        if isinstance(obs, dict):
                            if "refined_answer" in obs.keys():
                                refined_answer = obs.get("refined_answer", "")
                            else:
                                refined_answer = json.dumps(obs, ensure_ascii=False)
                        else:
                            refined_answer = str(obs)

                        if (
                            isinstance(obs, dict)
                            and "condition" in obs.keys()
                            and "api" in obs.keys()
                            and "search_result" in obs.keys()
                            and obs.get("search_result", "")
                        ):
                            logic_chain.append(
                                [obs.get("condition", ""), obs.get("api", ""), obs.get("search_result", "")]
                            )
                            if update_message:
                                update_logic_chain_and_messages(obs.get("condition", ""), logic_chain, messages)
                        # else:
                        #     logic_chain.append(refined_answer)

                    else:
                        refined_answer = obs.get("refined_answer", "")
                    messages.append(
                        {
                            "role": "tool",
                            "content": f"{refined_answer}",
                            "tool_id": tool_id,
                            # "tool_id": tools_call.id
                        }
                    )
                else:
                    # if message['role'] == 'assistant' and (message['content'].__contains__('未提供') or message['content'].__contains__('未能')):
                    #     must_contained_info, tokens_count, messages, response = run(query, tools, related_tables, update_message=False)
                    # else:
                    print_log("###对话结束###")
                    # logic_chain.append(message['content'])
                    # information = '\n'.join(logic_chain)
                    information = ""
                    for per_logic in logic_chain:
                        if type(per_logic) == list and len(per_logic) == 3:
                            information = (
                                information
                                + "根据:"
                                + str(per_logic[0])
                                + "和接口:"
                                + str(per_logic[1])
                                + ",查询到:"
                                + str(per_logic[2])
                                + "\n"
                            )
                        else:
                            information = information + str(per_logic) + "\n"
                    information = information.strip()
                    if (
                        query.__contains__("api")
                        or query.__contains__("API")
                        or query.__contains__("接口")
                        or query.__contains__("ＡＰＩ")
                    ):
                        final_prompt = prompt_final_result_without_API.format(
                            query=query, information=information, prompt_4_API=prompt_4_API
                        )
                    else:
                        final_prompt = prompt_final_result_without_API.format(
                            query=query, information=information, prompt_4_API=""
                        )
                    final_message = [{"role": "user", "content": final_prompt}]
                    response = call_glm(final_message, model="glm-4-0520")
                    # check_API(query, response, information)
                    retry_index = 10
                    break
            except Exception as e:
                print_log(e)
                time.sleep(4)
                break

    if retry_index == 10:
        return must_contained_info, tokens_count, messages, response, response.choices[0].message.content
    else:
        # final_message = [
        #     {"role": "system", "content": "你是一个法律专家，请根据你的专业知识回答用户的问题"},
        #     {"role": "user", "content": query}
        # ]
        # response = call_glm(final_message)
        # return [], tokens_count, [{"content": response.choices[0].message.content, "role": "assistant"}], response

        return must_contained_info, tokens_count, [{"content": query, "role": "assistant"}], query, query + "抱歉"


def process_query(all_tools, query, update_message=True, suggested_logic_chain=False, use_full_tools=False):
    route = predict_direct_or_tools(query["question"], False)
    # response = parse_json_from_response(direct_or_tools)["category_name"]
    response = ""
    if route == "诉讼书":
        result = run_sue(query["question"], None, None)
    elif route == "整合报告":
        # result = run_report(query["question"], None)

        related_tables = get_related_tables(query["question"])
        related_tables = parse_json_from_response(related_tables)["table_name"]
        enhance_tables(related_tables, query)
        tools = route_tools(related_tables, all_tools)
        tools.append(all_tools.get("get_integrated_report"))
        if use_full_tools:
            tools = []
            for key, tool in all_tools.items():
                tools.append(tool)
        response = answer_report.run(
            query["question"],
            tools,
            related_tables,
            update_message=update_message,
            suggested_logic_chain=suggested_logic_chain,
        )
        # response = run(query["question"], tools, related_tables, False)

        # result = response[-1].choices[0].message.content.replace('答案：', '')
        result = response[-1].replace("答案：", "")
        result = final_post_process(result)
        must_contained_info = response[0]
        for condition in must_contained_info:
            condition = final_post_process(condition)
            if result.__contains__(condition):
                continue
            else:
                print_log("++++++++++++++++++++++++++++++++")
                print_log("missed condition: " + condition)
                print_log("++++++++++++++++++++++++++++++++")
                result = result + "." + condition
    else:
        related_tables = get_related_tables(query["question"])
        related_tables = parse_json_from_response(related_tables)["table_name"]
        enhance_tables(related_tables, query)
        tools = route_tools(related_tables, all_tools)
        if use_full_tools:
            tools = []
            for key, tool in all_tools.items():
                tools.append(tool)
        response = run(
            query["question"],
            tools,
            related_tables,
            update_message=update_message,
            suggested_logic_chain=suggested_logic_chain,
        )
        # response = run(query["question"], tools, related_tables, False)

        # result = response[-1].choices[0].message.content.replace('答案：', '')
        result = response[-1].replace("答案：", "")
        result = final_post_process(result)
        must_contained_info = response[0]
        for condition in must_contained_info:
            condition = final_post_process(condition)
            if result.__contains__(condition):
                continue
            else:
                print_log("++++++++++++++++++++++++++++++++")
                print_log("missed condition: " + condition)
                print_log("++++++++++++++++++++++++++++++++")
                result = result + "." + condition
    result = final_post_process(result)

    # pass
    # # result = ''
    content = {"id": query["id"], "question": query["question"], "answer": result}
    # order_queue.put((query["id"],content))
    return content


def process_query_and_put_in_queue(all_tools, query, order_queue, update_message=True, use_full_tools=False):
    try:
        content = process_query(all_tools, query, update_message=update_message, use_full_tools=use_full_tools)
        order_queue.put((query["id"], content))
    except Exception as e:
        content = {"id": query["id"], "question": query["question"], "answer": query["question"] + "抱歉"}
        order_queue.put((query["id"], content))
        print(f"Error processing query {query['id']}: {e}")


def process_queries_in_parallel(all_tools, queries, update_message=True, use_full_tools=False):
    order_queue = Queue()
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(
                process_query_and_put_in_queue, all_tools, query, order_queue, update_message, use_full_tools
            )
            for query in queries
        ]

        for future in tqdm(as_completed(futures), total=len(queries)):
            pass  # 进度条更新

    results_in_order = sorted([order_queue.get() for _ in queries], key=lambda x: x[0])
    return results_in_order


def refine_results(all_tools, result_file, update_message):
    refined_results = []
    results = read_jsonl(result_file)
    for result in results:
        answer = result["answer"]
        if (
            answer.__contains__("抱歉")
            or answer.__contains__("未提供")
            or answer.__contains__("没提供")
            or answer.__contains__("无法")
            or answer.__contains__("未在")
            or answer.__contains__("未查询")
            or answer.__contains__("未能")
            or answer == ""
        ):
            content = process_query(all_tools, result, update_message=update_message)
            refined_results.append(content)
        else:
            refined_results.append(result)
    return refined_results


def get_incorrect_results(result_file):
    incorrect_results = []
    incorrect_ids = []
    results = read_jsonl(result_file)
    for result in results:
        answer = result["answer"]
        if check_incorrect_answer(answer):
            # if answer.__contains__('抱歉') or answer.__contains__('未提供') or answer.__contains__('没提供') or answer.__contains__('无法') or answer.__contains__('未在') or answer.__contains__('未查询') or answer.__contains__('未能') or answer == '':
            incorrect_results.append(result)
            incorrect_ids.append(result["id"])
    return incorrect_results, incorrect_ids


def check_incorrect_answer(answer):
    if answer == "":
        return True
    incorrect_keywords = ["抱歉", "未提供", "没提供", "无法", "未在", "未查询", "未能", "建议"]
    for keyword in incorrect_keywords:
        if answer.__contains__(keyword):
            return True
    return False


def print_answer(result_file):
    results = read_jsonl(result_file)
    online_results = json.dumps(results, ensure_ascii=False)
    print(online_results)


if __name__ == "__main__":
    if isLocal:
        question_file = "./data/questions/question_c_more.json"
        question_file = "./data/questions/question_c_report.json"
        result_file = "data/results/fa_1.json"
        result_file = "data/results/fa_2.json"

        queries = read_jsonl(question_file)

        print_log("Start generating answers...")
        all_tools = get_tools()
        print_log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        for query in tqdm(queries):
            # # # 如果中断，可以从这里开始
            if query["id"] < 170:
                continue
            content = process_query(all_tools, query, use_full_tools=True)
            with jsonlines.open(result_file, "a") as json_file:
                json_file.write(content)

        print_log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    else:
        question_file = "../assets/question_d.json"
        result_file = "/app/result.json"

        queries = read_jsonl(question_file)
        # 生成答案
        print_log("Start generating answers...")

        all_tools = get_tools()

        query_1 = queries[:50]
        print_log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        results_in_order = process_queries_in_parallel(all_tools, query_1)
        with jsonlines.open(result_file, "a") as json_file:
            for _, content in results_in_order:
                json_file.write(content)

        query_2 = queries[50:100]
        results_in_order = process_queries_in_parallel(all_tools, query_2)
        with jsonlines.open(result_file, "a") as json_file:
            for _, content in results_in_order:
                json_file.write(content)

        query_3 = queries[100:150]
        results_in_order = process_queries_in_parallel(all_tools, query_3)
        with jsonlines.open(result_file, "a") as json_file:
            for _, content in results_in_order:
                json_file.write(content)

        query_4 = queries[150:]
        results_in_order = process_queries_in_parallel(all_tools, query_4)
        with jsonlines.open(result_file, "a") as json_file:
            for _, content in results_in_order:
                json_file.write(content)

        print("nick first")
        results = read_jsonl(result_file)
        results_without_question = []
        for result in results:
            results_without_question.append({"id": result["id"], "answer": result["answer"]})
        online_results = json.dumps(results_without_question, ensure_ascii=False)
        print(online_results)
        incorrect_answers, incorrect_ids = get_incorrect_results(result_file)
        print("incorrect number: " + str(len(incorrect_ids)))

        part_results_in_order = process_queries_in_parallel(all_tools, incorrect_answers, update_message=False)
        id_content_dict = {}
        for part_result in part_results_in_order:
            id_content_dict[part_result[0]] = part_result[1]

        with jsonlines.open(result_file, "w") as json_file:
            for content in results:
                if content["id"] in id_content_dict:
                    content = id_content_dict[content["id"]]
                json_file.write(content)
        print("nick second")
        results = read_jsonl(result_file)
        incorrect_answers, incorrect_ids = get_incorrect_results(result_file)
        results_without_question = []
        for result in results:
            if result["id"] in id_content_dict and (not result["id"] in incorrect_ids):
                results_without_question.append({"id": result["id"], "answer": result["answer"]})
        online_results = json.dumps(results_without_question, ensure_ascii=False)
        print(online_results)
        incorrect_answers, incorrect_ids = get_incorrect_results(result_file)
        print("incorrect number: " + str(len(incorrect_ids)))

        part_results_in_order = process_queries_in_parallel(all_tools, incorrect_answers, update_message=True)
        id_content_dict = {}
        for part_result in part_results_in_order:
            id_content_dict[part_result[0]] = part_result[1]

        with jsonlines.open(result_file, "w") as json_file:
            for content in results:
                if content["id"] in id_content_dict:
                    if not check_incorrect_answer(id_content_dict[content["id"]]["answer"]):
                        content = id_content_dict[content["id"]]
                json_file.write(content)
        print("nick third")
        results = read_jsonl(result_file)
        incorrect_answers, incorrect_ids = get_incorrect_results(result_file)
        results_without_question = []
        for result in results:
            if result["id"] in id_content_dict and (not result["id"] in incorrect_ids):
                results_without_question.append({"id": result["id"], "answer": result["answer"]})
        online_results = json.dumps(results_without_question, ensure_ascii=False)
        print(online_results)
        incorrect_answers, incorrect_ids = get_incorrect_results(result_file)
        print("incorrect number: " + str(len(incorrect_ids)))
        print_log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
