import json

from knowledge.prompt import execute
from Agent.llm import llm
import re
from kernel import CodeKernel, run_code
from knowledge.api_info import APIS
from knowledge.tools2json import TOOLS, TOOLS_DESC


class Executor:

    def __init__(self, question, flow, reference_code='', recall_code=None, conditions='', max_try_num=5):
        self.code_kernel = CodeKernel()
        postable = []
        for i in flow:
            if 'table_name' in i:
                postable.append(i['table_name'])

        pos_api = [i for i in APIS if
                   i['数据表'] in postable or i['数据表'] == 'Any' or i['路由'] in str(flow) + question]
        self.reference_code = f'你可以参考的代码为：{reference_code},以上代码参数为正确参数，遇到相似问题如果用户问题和规划和上述不一致，以上述代码参数为准' if reference_code else ''
        self.answer = None
        self.question = question
        self.qa_content = question + "解答步骤" + conditions
        self.step = None
        self.try_num = 0
        self.err_num = 0
        self.final_answer = None
        self.flow = flow
        self.sys_prompt = execute.format(
            pos_api) + self.reference_code + f'\n需要解决的问题为：{self.question},' + '\n用户已经规划好了方案，请在用户的指引下一步步编写python代码，不要抢答'

        self.messages = [
            {'role': 'system',
             'content': self.sys_prompt}]

        self.reduce_code_message_flag = False  # 代码输出是否被缩减

        self.err_msg_inx = 0
        self.recall = recall_code
        self.max_return_len = 0
        self.code_answer = []
        self.max_try_num = max_try_num
        self.code = None
        self.completed_step = [0]
        self.is_name_err = ''

        run_code(
            'from api import call_api\nimport re,json\nfrom math import inf\nfrom copy import deepcopy\nimport jieba.analyse\nimport contextlib\nimport io\njieba.analyse.textrank("111")\n',
            self.code_kernel, True)

    def summary_message(self):
        python_code = self.code_kernel.cache_code

        for x, y in zip(TOOLS, TOOLS_DESC):
            python_code = python_code.replace(x['code'], y['code'])

        self.messages = [
            {'role': 'system',
             'content': self.sys_prompt},
            {'role': 'system', 'content': f"""
当前ipython缓存代码为：
```python
{python_code}
```
---
当前执行日志为：
{self.qa_content}
---
执行后面的任务参考此日志ipython中代码已经运行成功，变量可以使用。,注意，已有的参数不要重新定义，更不要设置成示例参数。
"""}]

    def check_add_api(self):

        content = self.get_all_messages_content()
        pos_api = [i for i in APIS if i['路由'] in content]

        self.sys_prompt = execute.format(
            pos_api) + self.reference_code + f'\n需要解决的问题为：{self.question},' + '\n用户已经规划好了方案，请在用户的指引下一步步编写python代码，不要抢答'

        self.messages[0]['content'] = self.sys_prompt

    def add_code_message(self, code_info):
        if '中间内容省略，如需查看，请缩减输出内容后重新打印' in code_info:
            self.reduce_code_message_flag = True
        # print('当前执行结果为', code_info)
        # print('要匹配的代码为', self.code)

        if 'API info' in code_info and not re.search('for \w+ in', self.code, re.DOTALL):
            if '注意本轮可能查不到内容，如果返回报错，则记为无内容' in self.messages[-2]['content']:
                self.messages.append({
                    'role': 'user',
                    'content': f'API返回内容：无'})
            else:
                code_info = re.split('----------+', code_info, re.DOTALL)[0]
                self.messages.append({
                    'role': 'user',
                    'content': f'API返回内容：{code_info}\n你调用API的方式有问题，请参考说明进行修改，修改后的代码在```python ```内。'})

            return {}

        if 'Traceback' in code_info and 'KeyError' in code_info:
            if self.try_num < 2:
                self.messages.append({
                    'role': 'user',
                    'content': code_info + f'''
你在之前的步骤中忘记在need_fields加入这个字段，请重新加入这个字段然后尝试，接下来的步骤一次完成获取和当前步骤。注意分析是在哪一步获取的这个结果。
'''})
                return {}

        if ('Traceback' in code_info or 'Error' in code_info) and not re.search('for \w+ in', self.code, re.DOTALL):
            if self.try_num < 2:
                self.messages.append({
                    'role': 'user',
                    'content': code_info + f'''请分析以上报错信息，然后重新编写代码，或者给出查看参数的代码确认参数，或者得到信息后直接赋值并打印。
    注意，代码在ipython中运行，参数已经保存，对于非查询任务，禁止设置成示例参数，尤其是对于列表类数据，修改后的代码在```python ```内。
    对于查询任务，你可以直接给参数赋值，对于地点任务，你可以直接提取，如果无需编码也能完成，例如从文本中判断最高级别法院，判断胜诉方等
    你也可以跳过编码步骤，直接给出答案并赋值。
    '''})
                return {}
            else:
                self.messages.append({
                    'role': 'user',
                    'content': code_info + f'''
你的代码还是报错，为了让你专注编码，我已经清空了ipython，但是保留了辅助函数，你需要分析现有任务，从之前的日志中，将可以使用的结果赋值（列表除外，隐藏结果的除外），并重新编码。
你会先分析已知条件，以及之前的报错原因，然后进行编码。
'''})
                return {}

        # 这里应该是正常的
        self.code_answer.append(code_info)

        #         if '结果过长，中间内容省略' in code_info or '只显示前三条' in code_info:
        #             msg_tip = '''
        # ---\n 任务已完成：\n```answer \n[xx结果]已保存[保存的参数名]，你可以直接使用此参数\n```\nipython参数已保存[保存的参数名]\n---\n的格式回答问题，注意保存的参数名不要搞错
        # '''
        #         else:
        msg_tip = '''
---\n任务已完成\nipython参数已保存`保存的参数名`\n---\n的格式回答问题。
'''
        self.max_return_len = max(len(code_info), self.max_return_len)
        self.messages.append({
            'role': 'user',
            'content': code_info + f'''
以上是执行结果，请判断{self.step}是否完成，请推理判断。
如果任务完成，请你按照：
{msg_tip}
如果运行失败你有以下几个选择：
1. 如果不符合预期，你需要继续完成{self.step}，但是只限于{self.step}内，请不要擅自进行下一步。
2. 不知道原因的错误你可以先查看参数，列表类参数你只可以查看前三条，或者使用try except的形式打印错误参数.
3. 遇到非查询类复杂错误后换一种方法执行不要尝试修复之前的错误代码
4. 切记不可跳跃step直接回答问题。
5. 你仅仅可以再使用call_api函数时使用自己定义的参数，对于其他操作，必须使用call_api返回的参数
注意：代码在```python ```内，其余答案直接输出，不要使用md格式。请判断是否符合预期后选择执行。 另外，你无需执行下一步。
'''})
        return {}

    def add_log_message(self):
        self.messages.append({"role": 'user',
                              'content': '''
请将之前的执行步骤按照日志的格式整理，如果成功请将之前的过程总结成简要的流程，只保留正确的步骤，方便以后查看，
如果不成功，写出执行步骤以及失败原因,注意保留接口路由和参数。'''})

    def add_err_message(self):
        self.err_num += 1
        self.err_msg_inx = len(self.messages)

        if self.qa_content != '':
            self.messages.append({
                'role': 'user', 'content': f'''
统一社会信用代码为91420100568359390C的公司，企业参保人数有多少? 查询到了统一社会信用代码下的公司为武汉光庭信息技术股份有限公司则改写为：武汉光庭信息技术股份有限公司参保人数有多少?
即将得到的信息加入问题使得问题更加简单，注意你会检查之前的结果，禁止将假设的结果当成已知条件，例如公司A,事务所A。
按照以下json格式输出：
```json
{{
"已知条件":"列举已知条件如查询到的结果，题目字段错误等",
"改写后的问题":"将已知条件带入问题并改写"
}}
```
基于之前的运行结果，改写问题：{self.question}
'''
            })
        else:
            self.messages.append({"role": 'user',
                                  'content': '''请说明之前的执行步骤出现了哪些问题，请先列出之前的流程，然后说明问题，然后说明最开始流程可能有的问题，我将解答后重新规划执行步骤,你只需要列出执行流程，不需要列出解决方案。'''})

    def add_format_message(self):
        self.messages.append({"role": 'user',
                              'content': f'请判断{self.step}任务是否完成，完成的话返回任务已完成，没有完成则继续编码完成任务，无法完成任务则返回`无法完成`。'})

    def get_all_messages_content(self):

        content = ''
        for i in self.messages:
            content += f'{i["role"]}:{i["content"]}\n\n'

        return content

    def handle_one_message(self):
        self.check_add_api()
        exec_answer = llm(self.messages)
        if '任务已完成' in exec_answer and '无法' not in exec_answer and \
                '```python' not in exec_answer and '# 作用' not in exec_answer:
            '''
            -1 任务完成 assistant   -2  user 给的 code结果 -3 assistant 的代码  -4 可能是提示 -5 ass 代码 
            '''

            if len(self.messages) > 5:
                if 'API info' in self.messages[-4]['content']:
                    with open('exp_raw.jsonl', 'a', encoding='utf8') as f:
                        f.write(json.dumps(self.messages[-5:]))
                        f.write('\n')

            if '任务已完成\nipython' in exec_answer:
                text = ''
                for i in self.code_answer[-1].split('\n'):
                    if i and '重要消息' not in i:
                        text += i
                        text += '\n'
                if text:
                    exec_answer = exec_answer.replace('任务已完成\nipython',
                                                      f"任务已完成:\n```answer\n{text}```\nipython")

            return {"run": 0, 'step_answer': exec_answer}
        elif self.try_num >= self.max_try_num:
            return {'run': 3, 'error_log': 1}
        elif '已确定无假设数据' in exec_answer:
            self.messages.pop()
            self.messages.pop()
            self.messages[-1]['content'] = self.messages[-1]['content'] + '\n<safe>'
            exec_answer = self.messages[-1]['content']

        elif exec_answer.startswith('# 作用：'):
            self.code = exec_answer
            code_info = run_code(exec_answer, self.code_kernel, True)
            if not code_info.strip():
                self.messages.append({'role': 'user',
                                      'content': '你没有打印出有用信息，请将你需要查看的参数使用```python print(arg) # 替换为你想要查看的参数 ``` 打印出来)'})

            if not isinstance(code_info, str):
                print('code_info+++++++>>>>>>>>>', code_info)
            code_info = str(code_info)

            if 'error_log' in self.add_code_message(code_info):
                return {'run': 3, 'error_log': 1}
            return {"run": 1}
        elif '```python' in exec_answer:
            self.code = exec_answer
            code_info = run_code(exec_answer, self.code_kernel)
            if not code_info.strip():
                self.messages.append({'role': 'user',
                                      'content': '你没有打印出有用信息，请将你需要查看的参数使用```python print(arg) # 替换为你想要查看的参数 ``` 打印出来)'})

            if not isinstance(code_info, str):
                print('code_info+++++++>>>>>>>>>', code_info)
            code_info = str(code_info)

            if 'error_log' in self.add_code_message(code_info):
                return {'run': 3, 'error_log': 1}
            return {"run": 1}
        elif '无法完成' in exec_answer:
            return {'run': 3, 'error_log': 1}

        elif '无需执行' in exec_answer:
            return {"run": 0, 'step_answer': exec_answer}
        else:
            self.add_format_message()
            return {"run": 1}

    def set_step_prompt(self, step_info):
        self.step = f"{step_info['step']}.{step_info['goal']}"
        msg = ''
        if step_info['is_necessary'] == 'necessary':
            msg += '本轮必须查询到内容，如果查询到内容，视为查询完整，可以进行下一步\n'
        else:
            msg += '注意本轮可能查不到内容，如果返回报错，则记为无内容，并回复：无需执行“”\n'
        # if '如果' in self.step:
        #     msg += '注意本轮存在假设可能无需执行，无需执行的话请回复”无需执行“\n'
        if step_info['type'] != '查询' and re.search('确定|判断|获取', str(step_info)):
            msg += '如果你需要进行自然语言判定任务，无需编码，自行判断并赋值即可'
        functions = []
        for code, desc in zip(TOOLS, TOOLS_DESC):
            if re.search(code['pattern'], self.get_all_messages_content()):
                functions.append(desc['code'])
                run_code(code['code'], self.code_kernel, True)

        ff = "\n\n".join(functions)

        if step_info['type'] == '查询':
            if re.search(TOOLS[0]['pattern'], step_info['suggestion']):
                fff = TOOLS_DESC[0]['code']
                run_code(TOOLS[0]['code'], self.code_kernel, True)
                msg += f'\n\n以下辅助函数已经定义，你可以直接使用，无需import，如果有用，优先使用辅助函数 \n{fff}'
            prompt = f'''
你要执行的是查询操作，查询任务为：{self.step}。{msg}   
你应该仔细阅读接口文档，如果有历史执行记录，你应该从历史记录中找到相关记录，找到参数，如果你不确定之前参数的数据结构，你可以重新构造新的参数对象。  
请参照以下建议执行：{step_info['suggestion']},注意结果需要赋值并且命名合理。
{self.is_name_err}
'''
        elif step_info['type'] == '自然语言推理':
            prompt = f'''
你要执行的是自然语言推理操作，任务为：{self.step}
你要使用自然语言进行推理，这个步骤比较特殊，无法使用编码完成，请从之前的结果中，推理出正确答案，并且给python变量赋值。请开始编码，直接赋值即可
'''

        else:
            prompt = f'''
可能使用的辅助函数如下：
{ff}
计算接口示例如下：
---
# /get_sum 示例
# 设：list包含dict['涉案金额']
num_list = [i['涉案金额'] for i in your_list if i['涉案金额'] not in ['-','',None]] # 请使用这个过滤掉空值
total_amount = call_api('/get_sum',num_list,'求和')
# /rank 示例
# 排序接口参数，接口会自动转化，并去除无效值
route = '/rank'
param = {{
    "data_list": your_list,
    "key": '涉案金额',
    "is_desc": True  # 降序排序
}}
# 排序并获取结果
sorted_case_numbers = call_api(route, param, '按照涉案金额排序裁判文书')
# 获取涉案金额第二高的案件的案号
second_highest_amount_case_number = sorted_case_numbers[1]['案号']
你要注意的是，所有返回的数字都是字符串形式。如果你不是通过接口计算，使用map_str_to_num转为数值。
---
需要注意的是：请你一定使用在ipython中保存的参数，不要重新定义，无需import。   
如果是其他类型的计算，请参考以上处理方法，记得转化为数值类型。
你应该仔细阅读函数的文档字符串，确保传参正确，定义函数函数已经运行，你可以直接调用，过滤函数的第一个参数是你之前获得的全量结果list，对此参数你无需额外处理。
对于无法直接使用以上函数过滤的操作，你可以先使用以上函数得到部分结果，然后自己再次进行筛选，得到答案，并保存为新的参数。     
{msg}
请参照以下建议执行：{step_info['suggestion']}  
注意先从历史记录中，找到你需要的需要过滤或计算的结果参数，你的计算结果需要使用print打印出来，在打印结果前先打印结果说明。
你要执行的是过滤或计算操作，具体任务为：{self.step},请仅完成当前任务。
'''
        return prompt

    def handle_one_step(self, step_info):
        if not set(step_info['base_on_step']) <= set(self.completed_step):
            return {}

        self.try_num = 0
        prompt = self.set_step_prompt(step_info)

        self.messages.append(
            {'role': 'user', 'content': prompt})
        while True:
            res = self.handle_one_message()
            self.try_num += 1

            if step_info['type'] == '查询' and self.try_num > 1:
                self.is_name_err = '题目和中有可能有错误的名称，记得修复名称后查询'

            if res['run'] == 0:
                self.qa_content += f"""
--{step_info['step']}--
步骤：{step_info['goal']}
答案：{res['step_answer']}
---
"""
                self.summary_message()
                '单步骤执行成功'
                self.completed_step.append(step_info['step'])
                return res

            if 'error_log' in res:
                self.summary_message()
                # self.add_err_message()
                return {'error_log111': self.code_kernel.cache_code}

    def get_doc(self):
        # 确保 cache_code_list 不为空，并且至少有一个元素
        if self.code_kernel.cache_code_list:
            # 获取最后一个代码缓存项
            last_cache = self.code_kernel.cache_code_list[-1]
            print(last_cache)
            try:
                for i in last_cache['out'][-1].split('\n'):
                    if '查询结果为:' in i and 'doc' in i:
                        return eval(i.split('查询结果为:')[-1])['doc']
            except:
                return

    def get_final_answer(self):
        doc = self.get_doc()
        if doc:
            print('成功获取结果')
            return doc

        if self.err_msg_inx:
            self.messages = self.messages[:self.err_msg_inx]

        self.messages.append({'role': 'user',
                              'content': f'''根据以上对话尽可能输出{self.question}的答案，注意是答案不是代码，在回答问题时，你应该列出答案是如何推理得到的，
注意推理过程要基于代码运行结果的关键key：value，关键信息的参考源使用json格式列出。
答案为：根据xxx是xxx得到xxx，xxx的xxx是xxx所以答案为xxx
参考源：（这里注意只选择关键信息）
另外，如果是写作类型的题目，直接复述接口返回的内容，另外，不要回答关于API调用次数信息。
'''})
        return llm(self.messages)

    def get_executed_code(self):
        return self.code_kernel.cache_code

    def chat(self, user_message):
        self.messages.append({'role': 'user', 'content': user_message})
        print(llm(self.messages))


if __name__ == '__main__':
    code_kernel = CodeKernel()
