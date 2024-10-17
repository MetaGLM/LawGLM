from Agent.llm import llm, super_eval
# from llm import llm4 as llm
from knowledge.prompt import plan, TOOLS
import re
from knowledge.api_info import APIS, TABLES, API_DESC,APIS2
import json
from utils.arg_utils import check_suggestion
# from Agent.Recall import RecallQuestion
from knowledge.priori import TIPS
from utils.tips import get_tips
# recall_question = RecallQuestion(r'exp/exp_728.jsonl')

from knowledge.hard_sample import get_sample

class Planer:

    def __init__(self, question):
        self.question = question
        self.pos_table = []
        sample = get_sample(question)
        user_content = f"""问题：{question} 注意不要被示例混淆，请开始分析，并给出json。"""
        self.messages = [{'role': 'system', 'content': plan.format(json.dumps(TABLES, ensure_ascii=False, indent=1),
                                                                   json.dumps(APIS2, ensure_ascii=False, indent=1),
                                                                   TOOLS, sample)},
                         {'role': 'user', 'content': user_content}]

        # self.tips = tips
        self.plan_true = False

        self.init()
        for _ in range(2):
            if not self.plan_true:
                self.check_plan()



    def check_plan(self):
        suggestion_back = ''
        for i in self.plan_list:
            if i['type'] == '查询':
                suggestion_back += check_suggestion(i['suggestion'])
        if suggestion_back.strip():
            self.messages.append({'role': 'user', 'content': f'''
以上是计划json中suggestion字段的一些问题：
```
{suggestion_back}
```
错误大多数是没有使用标准的数据库字段或者使用的接口无法获得此字段，请考虑以上问题后，修复上面的问题，
如果need_fields有问题，则 确定是否需要此字段，例如有案号无需获得法院代字，然后看是否有相似字段，则使用相似字段，如果没有，则考虑重新规划解题路径。
重新输出分析结果
'''})
            self.init()
        else:
            self.plan_true = True

    def init(self):
        # self.plan_answer = recall_question.get_plan(self.question)
        self.plan_answer = llm(self.messages)
        # print(self.plan_answer)
        self.plan_list = super_eval(self.plan_answer)
        # self.pos_table = list(set([i['table_name'] for i in self.plan_list]))
        self.inx = 0
        self.flow = self.get_plan()

    def add_plan_message(self, message):

        self.messages.append({'role': 'user', 'content': f'''
之前的计划在执行中遇到了一些问题，以下是执行日志：```{message}```
计划:{ self.plan_list[self.inx-1]} 无法执行，你需要做的是，根据以及成功执行的代码，和无法执行的步骤，重新规划，
无法执行的愿意大多是因为：你没有将步骤拆分独立，need_fields缺失字段等，请将过滤和计算分开，并给出更具体的建议和更加独立的步骤和完整的need_fields,依旧按照以下格式输出
推理流程：
```md
xxx
```
更新后的步骤：
```json
[
 {{"step":1,"goal":"xxx","type":"查询/计算","suggestion"："xxx","table_name":"xxx","is_necessary": "necessary/unnecessary"}},
 {{"step":2,"goal":"xxx","type":"查询/计算","suggestion"："xxx","table_name":"xxx","is_necessary": "necessary/unnecessary"}}
  ...
]
```
'''})

    def get_plan(self):
        plan_str = ''
        for i in self.plan_list:
            plan_str += f"{i['step']}. {i['goal']}\n"
        return plan_str

    def get_next_step(self, message=None):

        if message == None:
            if self.inx < len(self.plan_list):
                step = self.plan_list[self.inx]
                self.inx += 1
                return step
            else:
                return None
        else:
            self.add_plan_message(message)
            self.init()
            step = self.get_next_step()
            return step

    # TODO 更复杂的计划过程
    def execute(self, message):
        # 第一次返回所有的plan，之后返回next_step
        if isinstance(message, dict):
            self.messages.append(message)
        else:
            self.messages.append({'role': 'user', 'content': message})

        _prompt = ''
        ...

    def get_api_answer(self):
        self.messages.append({
            'role': 'user',
            'content': f"请回答{self.question}中关于API调用的问题，备注：API串行的意思是有依赖的执行，即前一步必须依赖后一步，多少类API就是种类，用的API个数是调用了多少个,你在回答此类问题的时候要带上单位次，类或者个，如果使用了函数，除特别提示的次数，也算一次，请先分析后作答"
        })
        answer = llm(self.messages)
        return answer

    def get_all_plan(self, message):
        _prompt = '以上是执行情况，请分析执行情况后，重新规划'

    def get_api_num(self):
        from collections import defaultdict
        # 构建边列表
        edges = []
        for step in self.plan_list:
            for dependency in step["base_on_step"]:
                edges.append((dependency, step["step"]))
        # 打印边列表
        # for edge in edges:
        #     print(edge)
        # 构建邻接表
        graph = defaultdict(list)
        for u, v in edges:
            graph[u].append(v)
        # 找到所有的末节点
        all_nodes = set()
        for u, v in edges:
            all_nodes.add(u)
            all_nodes.add(v)

        end_nodes = all_nodes - set(graph.keys())

        # 找到所有的0节点
        incoming_edges = defaultdict(int)
        for u, v in edges:
            incoming_edges[v] += 1

        zero_nodes = [node for node in all_nodes if incoming_edges[node] == 0]

        # 从0开始找到所有路径
        def find_all_paths(graph, start, end_nodes):
            def dfs(node, path):
                if node in end_nodes:
                    paths.append(path)
                    return
                for neighbor in graph[node]:
                    dfs(neighbor, path + [neighbor])

            paths = []
            dfs(start, [start])
            return paths

        # 找到所有从0开始的路径
        start_node = 0
        paths_from_zero = find_all_paths(graph, start_node, end_nodes)

        # print("末节点:", end_nodes)
        # print("0节点:", zero_nodes)
        # print("从0开始到末节点的所有路径:")

        api_list = []
        path_api_num_max = 0
        for path in paths_from_zero:
            print(path)
            path_api_num = 0
            for inx in path:
                if inx>0:
                    suggestion = [i for i in self.plan_list if i['step'] == inx][0]['suggestion']
                    use_api = re.findall('/[a-z_]+|get_court_base_info_by_case_number',suggestion)
                    use_api = [i for i in use_api if i not in ['/rank','/get_sum']]
                    api_list.extend(use_api)
                    path_api_num+=len(use_api)
            path_api_num_max += path_api_num-1

        res = f'''
共使用了{len(set(api_list))}类api
调用了{len(api_list)}次
串行了{path_api_num_max}次
以上为计划调用，如果题目中有并行情况，例如询问子公司的地址等，则每个子公司都需要调用，此时，调用了多少次需要加上 子公司数量 - 1 例如有3个子公司，则需要在调用次数+2
'''
        return res