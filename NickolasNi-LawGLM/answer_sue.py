from pprint import pprint

from match_tools.tools_register import get_tools, dispatch_tool
from match_tools.post_process import post_process_tool_results, prompt_final_result_without_API, prompt_4_API
from match_tools.pre_process import pre_process_company_tools, check_tool_and_args
from model import call_glm
from utils import *
from prompts import system_sue_prompt
from config import *


def run_sue(query, tools, related_tables, update_message=True):
    tokens_count = 0
    sys_prompt = system_sue_prompt
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": query}]

    logic_chain = []
    must_contained_info = set()
    for i in range(10):
        print_log(f"##第{i}轮对话##")
        pprint_log(messages)
        print_log("#" * 10)
        print_log("\n")
        result = ""
        for _ in range(3):
            try:
                # response = call_glm(messages, model="glm-4-0520", tools=tools)
                # response = call_glm(messages, model="glm-4-0520", tools=tools, do_sample=False)
                response = call_glm(messages, model="glm-4-0520", tools=tools, temperature=0.11, top_p=0.11)
                message, response = parse_content_2_function_call(response.choices[0].message.content, response)
                tokens_count += response.usage.total_tokens
                # messages.append(response.choices[0].message.model_dump())
                messages.append(message)
                break
            except Exception as e:
                print_log(e)

        try:
            if response.choices[0].finish_reason == "tool_calls":
                # tools_call = response.choices[0].message.tool_calls[0]
                # tool_name = tools_call.function.name
                # args = tools_call.function.arguments

                tool_name = message["tool_calls"][0]["function"]["name"]
                args = message["tool_calls"][0]["function"]["arguments"]
                args = check_company_name(tool_name, args, logic_chain, must_contained_info)
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
                if message["role"] == "assistant" and (
                    message["content"].__contains__("未提供") or message["content"].__contains__("未能")
                ):
                    pass
                    # must_contained_info, tokens_count, messages, response = run(query, tools, related_tables, update_message=False)
                else:
                    print_log("###对话结束###")
                    # logic_chain.append(message['content'])
                    # information = '\n'.join(logic_chain)
                    parsed_args = parse_json_from_response(message.get("content", ""))

                    plaintiff_params = {
                        "query_conds": {"公司名称": parsed_args.get("原告单位", "")},
                        "need_fields": [],
                    }
                    plaintiff_api_result = http_api_call("get_company_info", plaintiff_params)
                    defendant_params = {
                        "query_conds": {"公司名称": parsed_args.get("被告单位", "")},
                        "need_fields": [],
                    }
                    defendant_api_result = http_api_call("get_company_info", defendant_params)
                    plaintiff_law_firm_params = {
                        "query_conds": {"律师事务所名称": parsed_args.get("原告律师事务所", "")},
                        "need_fields": [],
                    }
                    plaintiff_law_firm_api_result = http_api_call("get_lawfirm_info", plaintiff_law_firm_params)
                    defendant_law_firm_params = {
                        "query_conds": {"律师事务所名称": parsed_args.get("被告律师事务所", "")},
                        "need_fields": [],
                    }
                    defendant_law_firm_api_result = http_api_call("get_lawfirm_info", defendant_law_firm_params)

                    if (
                        plaintiff_api_result
                        and plaintiff_api_result.get("return")
                        and len(plaintiff_api_result.get("return"))
                        and defendant_api_result
                        and defendant_api_result.get("return")
                        and len(defendant_api_result.get("return"))
                        and plaintiff_law_firm_api_result
                        and plaintiff_law_firm_api_result.get("return")
                        and len(plaintiff_law_firm_api_result.get("return"))
                        and defendant_law_firm_api_result
                        and defendant_law_firm_api_result.get("return")
                        and len(defendant_law_firm_api_result.get("return"))
                    ):
                        plaintiff = plaintiff_api_result.get("return")[0]
                        defendant = defendant_api_result.get("return")[0]
                        plaintiff_law_firm = plaintiff_law_firm_api_result.get("return")[0]
                        defendant_law_firm = defendant_law_firm_api_result.get("return")[0]
                        if parsed_args.get("起诉状类别") == "法人起诉法人":
                            data = {
                                "原告": plaintiff.get("法人代表", ""),
                                "原告性别": "",
                                "原告生日": "",
                                "原告民族": "",
                                "原告工作单位": parsed_args.get("原告单位", ""),
                                "原告地址": plaintiff.get("注册地址", "") + plaintiff.get("办公地址", ""),
                                "原告联系方式": plaintiff.get("联系电话", ""),
                                "原告委托诉讼代理人": parsed_args.get("原告律师事务所", ""),
                                "原告委托诉讼代理人联系方式": plaintiff_law_firm.get("通讯电话", ""),
                                "被告": defendant.get("法人代表", ""),
                                "被告性别": "",
                                "被告生日": "",
                                "被告民族": "",
                                "被告工作单位": parsed_args.get("被告单位", ""),
                                "被告地址": defendant.get("注册地址", "") + defendant.get("办公地址", ""),
                                "被告联系方式": defendant.get("联系电话", ""),
                                "被告委托诉讼代理人": parsed_args.get("被告律师事务所", ""),
                                "被告委托诉讼代理人联系方式": defendant_law_firm.get("通讯电话", ""),
                                "诉讼请求": parsed_args.get("诉讼请求", ""),
                                "事实和理由": "",
                                "证据": "",
                                "法院名称": parsed_args.get("法院名称", ""),
                                "起诉日期": parsed_args.get("起诉日期", ""),
                            }
                            result = http_api_call_original("get_citizens_sue_citizens", data)
                        elif parsed_args.get("起诉状类别") == "公司起诉法人":
                            data = {
                                "原告": parsed_args.get("原告单位", ""),
                                "原告地址": plaintiff.get("注册地址", "") + plaintiff.get("办公地址", ""),
                                "原告法定代表人": plaintiff.get("法人代表", ""),
                                "原告联系方式": plaintiff.get("联系电话", ""),
                                "原告委托诉讼代理人": parsed_args.get("原告律师事务所", ""),
                                "原告委托诉讼代理人联系方式": plaintiff_law_firm.get("通讯电话", ""),
                                "被告": defendant.get("法人代表", ""),
                                "被告性别": "",
                                "被告生日": "",
                                "被告民族": "",
                                "被告工作单位": parsed_args.get("被告单位", ""),
                                "被告地址": defendant.get("注册地址", "") + defendant.get("办公地址", ""),
                                "被告联系方式": defendant.get("联系电话", ""),
                                "被告委托诉讼代理人": parsed_args.get("被告律师事务所", ""),
                                "被告委托诉讼代理人联系方式": defendant_law_firm.get("通讯电话", ""),
                                "诉讼请求": parsed_args.get("诉讼请求", ""),
                                "事实和理由": "",
                                "证据": "",
                                "法院名称": parsed_args.get("法院名称", ""),
                                "起诉日期": parsed_args.get("起诉日期", ""),
                            }
                            result = http_api_call_original("get_company_sue_citizens", data)
                        elif parsed_args.get("起诉状类别") == "法人起诉公司":
                            data = {
                                "原告": plaintiff.get("法人代表", ""),
                                "原告性别": "",
                                "原告生日": "",
                                "原告民族": "",
                                "原告工作单位": parsed_args.get("原告单位", ""),
                                "原告地址": plaintiff.get("注册地址", "") + plaintiff.get("办公地址", ""),
                                "原告联系方式": plaintiff.get("联系电话", ""),
                                "原告委托诉讼代理人": parsed_args.get("原告律师事务所", ""),
                                "原告委托诉讼代理人联系方式": plaintiff_law_firm.get("通讯电话", ""),
                                "被告": parsed_args.get("被告单位", ""),
                                "被告地址": defendant.get("注册地址", "") + defendant.get("办公地址", ""),
                                "被告法定代表人": defendant.get("法人代表", ""),
                                "被告联系方式": defendant.get("联系电话", ""),
                                "被告委托诉讼代理人": parsed_args.get("被告律师事务所", ""),
                                "被告委托诉讼代理人联系方式": defendant_law_firm.get("通讯电话", ""),
                                "诉讼请求": parsed_args.get("诉讼请求", ""),
                                "事实和理由": "",
                                "证据": "",
                                "法院名称": parsed_args.get("法院名称", ""),
                                "起诉日期": parsed_args.get("起诉日期", ""),
                            }
                            result = http_api_call_original("get_citizens_sue_company", data)
                        elif parsed_args.get("起诉状类别") == "公司起诉公司":
                            data = {
                                "原告": parsed_args.get("原告单位", ""),
                                "原告地址": plaintiff.get("注册地址", "") + plaintiff.get("办公地址", ""),
                                "原告法定代表人": plaintiff.get("法人代表", ""),
                                "原告联系方式": plaintiff.get("联系电话", ""),
                                "原告委托诉讼代理人": parsed_args.get("原告律师事务所", ""),
                                "原告委托诉讼代理人联系方式": plaintiff_law_firm.get("通讯电话", ""),
                                "被告": parsed_args.get("被告单位", ""),
                                "被告地址": defendant.get("注册地址", "") + defendant.get("办公地址", ""),
                                "被告法定代表人": defendant.get("法人代表", ""),
                                "被告联系方式": defendant.get("联系电话", ""),
                                "被告委托诉讼代理人": parsed_args.get("被告律师事务所", ""),
                                "被告委托诉讼代理人联系方式": defendant_law_firm.get("通讯电话", ""),
                                "诉讼请求": parsed_args.get("诉讼请求", ""),
                                "事实和理由": "",
                                "证据": "",
                                "法院名称": parsed_args.get("法院名称", ""),
                                "起诉日期": parsed_args.get("起诉日期", ""),
                            }
                            result = http_api_call_original("get_company_sue_company", data)
                        return result
        except Exception as e:
            final_message = [
                {"role": "system", "content": "你是一个法律专家，请根据你的专业知识回答用户的问题"},
                {"role": "user", "content": query},
            ]
            response = call_glm(final_message)
            return response.choices[0].message.content

    return result
