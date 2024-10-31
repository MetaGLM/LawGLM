from pprint import pprint
from tools.tools_register import dispatch_tool
from tools.tool_correction_info import simplied_tool_info
from llm.ChainWrapper import ChainWrapper
from llm.RetrieverWrapper import RetrieverWrapper
from llm.glm_llm import client
from utils import * 
from tools.tools_untils import parse_tool_call, check_and_edit_observation


class BattleAgent:
    
    def __init__(self, prompt:str , tools_retriever: RetrieverWrapper, planing_chain:ChainWrapper , inter_summary_chain:ChainWrapper, judge_chain:ChainWrapper, log_path:str, model_name: str ="glm-4"):
        self.client = client
        self.model_name = model_name
        self.system_prompt = prompt
        self.judge_chain = judge_chain
        self.planing_chain = planing_chain
        self.inter_summary_chain = inter_summary_chain
        self.tools_retriever = tools_retriever
        self.summary_list = []
        self.log_path = log_path

    def load_chain(self, chain_name: str) -> ChainWrapper:
        """
        Load a chain according to the chain name
        :param chain_name: The name of the chain
        """
        metadata = get_chain_metadata( self.prompt_folder / '{}.prompt'.format(chain_name))
        return ChainWrapper(self.prompt_folder  /  '{}.prompt'.format(chain_name),
                            metadata['parser_func'])
        
    def save_log(self, log):
        with open(self.log_path, 'a', encoding='utf-8') as f:
            print(log)
            if isinstance(log,dict):
                log = json.dumps(log, ensure_ascii=False, indent=4)
            elif isinstance(log,list):
                log = str(log)
            f.write(log + "\n")
            f.close() 
    
    
    def call_glm(self, messages, temperature=0.5,
             tools=None):
        web_tools = {
        "type": "web_search",
        "web_search": {
            "enable" : False,
            "search_query": False,
             "search_results": False
            },
        }
        tools.append(web_tools)
        response = self.client.chat.completions.create(
            model=self.model_name,  # 填写需要调用的模型名称
            messages=messages,
            temperature=temperature,
            top_p=0.1,
            tools=tools
        )
        # print(messages)
        # print(response.json())
        return response
    

    def output_daialog(self, messages):
        daialog = []
        for message in messages:
            # print()
            role = message.get('role', None)
            content = message.get('content', None)
            tool_calls = message.get('tool_calls', None)
            # print(tool_calls)
            # print(role, tool_calls)
            if role == "system":
                continue
            if role == "assistant":
                if tool_calls:
                    for tool in tool_calls:
                        func_name, args_dict_str = tool['function']['name'], tool['function']['arguments']
                        daialog.append(f"助手即将调用工具{func_name}，参数为{args_dict_str}")
                else:
                    daialog.append(f"助手回复：{content}")
            elif role == "user":
                daialog.append(f"用户提问：{content}")
            elif role == "tool":
                daialog.append(f"工具回复：{content}")
        return "\n".join(daialog)
    
    
    def make_plan(self, query, evidence ='',summary= ''):
        planing_dict = {
            "tools_info": simplied_tool_info,
            "question": query,
            'intermediate_results': summary,
            'judge_comment': evidence,
        }
        planing_res = self.planing_chain.invoke(planing_dict)
        plan = planing_res['plan']
        plan_tools = planing_res['tools']
        search_str = f'对问题:\n{query}，现在已有计划:\n{plan}，请根据计划调用工具'
        tools_search = self.tools_retriever.invoke_for_tools(search_str,plan_tools)
        return plan, tools_search
    
    def _invoke(self, query, tools, player_turn_num = 10):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        vaild_label = 0
        correction_flag = False
        error_nums = 0
        last_asistant_messgae = ""
        for i in range(player_turn_num):
            
            ### 选手开始行动做出调用工具指令/回答总结
            for _ in range(3):
                try:
                    response = self.call_glm(messages, tools=tools)
                    response_str = response.choices[0].message.content
                    messages.append(response.choices[0].message.model_dump())
                    vaild_label += 1
                    self.save_log(response_str)
                    break
                except Exception as e:
                    print(str(e))
             
            if response.choices[0].finish_reason == "tool_calls":
                #GLM4 工具正常调用工具
                tools_call = response.choices[0].message.tool_calls[0]
                tool_name = tools_call.function.name
                args = tools_call.function.arguments
                self.save_log(f"调用工具名称{tool_name}")
                self.save_log(f"调用工具参数{args}")
                obs = dispatch_tool(tool_name, args, "007")
                correction_flag, checked_obs = check_and_edit_observation(tool_name, obs)
                vaild_label += 1   
                if correction_flag:
                    error_nums += 1
                    vaild_label -= 2
                    if error_nums > 2:
                        break 
                elif not correction_flag or error_nums > 2 :
                    error_nums = 0
                    last_asistant_messgae= messages[-1]
                    messages = messages[:vaild_label]
                    messages.append(last_asistant_messgae)
                messages.append({
                        "role": "tool", 
                        "content": f"{checked_obs}",
                        "tool_id": tools_call.id
                    })
                current_assistant_message = f'助手即将调用工具{tool_name}，参数为{args}'
                if current_assistant_message == last_asistant_messgae:
                    break
                else:
                    last_asistant_messgae = current_assistant_message
                self.save_log(f"选手第{i}轮QA")
                self.save_log(messages[-1])
            elif "python" in response_str:
                #GLM4 工具非正常调用工具
                func_name, args_dict = parse_tool_call(response_str)
                self.save_log(f"PARSED调用python函数名称{func_name}" )
                self.save_log(f"PARSED调用python函数参数{args_dict}" )
                obs = dispatch_tool(func_name, args_dict, "007")
                correction_flag, checked_obs = check_and_edit_observation(func_name, obs)
                vaild_label += 1   
                if correction_flag:
                    error_nums += 1
                    vaild_label -= 2
                    if error_nums > 2:
                            break
                elif not correction_flag :
                    error_nums = 0
                    last_asistant_messgae= messages[-1]
                    messages = messages[:vaild_label]
                    messages.append(last_asistant_messgae)
                    
                messages.append({
                        "role": "tool", 
                        "content": f"{checked_obs}",
                        "tool_id": "python_tool"
                    })
                self.save_log(f"选手第{i}轮QA")
                self.save_log(messages[-1])
                current_assistant_message = f'助手即将调用工具{func_name}，参数为{args_dict}'
                if current_assistant_message == last_asistant_messgae:
                    break
                else:
                    last_asistant_messgae = current_assistant_message
            else:
                self.save_log(f"选手第{i}轮QA")
                self.save_log(messages[-1])
                break 
                  
        return messages
        
    
    
    
    def invoke(self, query, judge_turn_num = 15, player_turn_num = 10):
        ###裁判裁定的上线 k
        self.summary_list = []
        judge_remark = ""
        inter_summary = ""
        for i in range(judge_turn_num):
            ##选手开始做计划
            for  k in range(4):
                try:
                    plan, tools_search = self.make_plan(query, inter_summary)
                    break 
                except:
                    if k == 3:
                        return "",""
                    else:
                        break 
            player_input =  f"###现有问题:{query}\n ###已有的中间步骤:{inter_summary}\n###现有计划为{plan}"
            self.save_log(f"第{i}轮裁判判定，选手输入为{player_input}")
            ##选手开始行动
            messages = self._invoke(player_input, tools_search,player_turn_num)
            daialog = self.output_daialog(messages)
            judge_dict = {
                'tools_info': simplied_tool_info,
                'question': query,
                'intermediate_results':inter_summary,
                'answer_process':daialog
            }
            #裁判开始回复
            judge_res = self.judge_chain.invoke(judge_dict)
            self.save_log(f"###第{i}轮裁判判定：裁判回复为\n{judge_res}" )
            judge = judge_res['judge']
            judge_remark = judge_res['remark']
            
            #阶段性总结： 提取出daialog中的关键中间步骤信息。
            inter_summary_dict = {
                'question': query,
                'answer_process':daialog,
                'intermediate_results':inter_summary,
                'judge_comment': judge_remark
            }
            inter_summary  = self.inter_summary_chain.invoke(inter_summary_dict).content
            self.save_log(f"###第{i}轮裁判判定：总结回复为\n{inter_summary}" )
            
            self.summary_list.append(inter_summary)
            if judge.lower() == "yes":
                break 
        
        return self.summary_list[-1], messages[-1]['content']
            
    
    
    
    
    
    


