from knowledge.prompt import runner_prompt
from Agent.llm import llm
from kernel import CodeKernel,run_code
import re


class Runner:
    #  使用之前AI完成的代码 效果不好
    def __init__(self, question,recall):
        self.code_kernel = CodeKernel()
        self.sys_prompt = runner_prompt
        self.question = question
        self.code_info = ''
        self.recall = recall
        self.build_messages()

    def build_messages(self):
        docs = self.recall.recall_code_by_num(self.question)
        run_code('from api import search,search_batch\nimport json\nimport re\n\n', self.code_kernel,True)
        doc_text = ''
        for i in docs:
            print(i['code'])
            doc_text += i['code']
            doc_text += '\n'
            doc_text += i['example']
            doc_text += '\n'
            run_code(i['code'],self.code_kernel,True)

        self.messages = [
            {'role': 'system',
             'content': runner_prompt.format(doc_text)}]
        # print('\n'*100)
    def judge_code_info(self):
        if 'API info' in self.code_info:
            return False
        if 'Traceback' in self.code_info or 'Error' in self.code_info:
            return False
        return True

    def handle_one_message(self):
        # 代码运行成功返回 0 尝试2次
        exec_answer = llm(self.messages)
        print(exec_answer)
        if '```python' in exec_answer or re.match('[a-zA-Z_]+',exec_answer):  # 一般就第一次带
            is_code = '```python' not in exec_answer

            self.code_info = run_code(exec_answer, self.code_kernel,is_code)
            if not self.code_info.strip(): # 没有打印，不太可能出现
                self.messages.append({'role': 'user',
                                      'content': '你没有打印出有用信息，请将你需要查看的参数使用```python print(arg) #替换为你想要查看的参数 ``` 打印出来)'})
                return {'run':1}
            if self.judge_code_info():
                # 运行成功
                self.messages.append({'role': 'user',
                                      'content': f'运行结果为：{self.code_info}' + f'请检查运行结果，是否符合预期，答案不足视为正确答案，如果是，立即停止编码，根据结果输出{self.question}的答案，如果信息不匹配，则回答"答案不可信"。\n答案为：'})
                return {'run': 1}
            else:

                self.messages.append({'role': 'user',
                                      'content': f'运行结果为：{self.code_info}' + f'运行出错，请尝试重新编码，你也可以仿照之前的函数重写并执行，得到你想要的答案。'})

                return {'run': 1}
        else:
            return {'run': 0}  # 没有代码,说明已经得到了答案

    def handle_question(self):
        # 接受plan给的一个提示，然后获取一个step_answer
        self.messages.append(
            {'role': 'user',
             'content': f"用户问题：{self.question}"})

        # 这里只要跑通了，就算运行成功。
        for _ in range(3):
            res = self.handle_one_message()

            if res['run'] ==0:  # 没有代码
                break


        function_name = re.findall('\s*(\w+)\s*\(\s*\)(.*)',self.messages[-1]['content'])



        return self.messages[-1]['content'],function_name


if __name__ == '__main__':
    import json
    from Agent.Recall import CoderRecall
    function_list = []
    with open('data/function.jsonl', encoding='utf8') as f:
        for i in f:
            function_list.append(json.loads(i))

    recall_code = CoderRecall(function_list)

    e = Executor('请问Beijing Comens New Materials Co., Ltd.有哪些子公司？参股比例分别是多少？',recall_code)
    m,f = e.handle_question()
    print( m,f)