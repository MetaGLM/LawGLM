# coding=utf-8

import re
import os
from io import StringIO
from contextlib import redirect_stdout
from contextlib import redirect_stderr
from utils_except import *
import traceback
import os
import logging
from logging.handlers import TimedRotatingFileHandler
def create_timed_rotating_log(path, name):
    """"""
    logging.getLogger().handlers.clear()
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(path,
                                       when="d",
                                       interval=1,
                                       backupCount=360)
    
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    #logger.addHandler(handler)
    logger.handlers[:] = [handler]
    logger.info("server restarted, init logger")

import datetime
#!mkdir logs
def init_log(prefix='a'):
    logdir = f"./logs/timelog{prefix}_{datetime.datetime.now().strftime('%Y%m%d')}"
    if os.path.isfile(logdir): os.remove(logdir)
    create_timed_rotating_log(logdir, "default")
    logdir = f"./logs/timelog{prefix}_code_{datetime.datetime.now().strftime('%Y%m%d')}"
    if os.path.isfile(logdir): os.remove(logdir)
    create_timed_rotating_log(logdir, "codes")
    logdir = f"./logs/timelog{prefix}_clean_{datetime.datetime.now().strftime('%Y%m%d')}"
    if os.path.isfile(logdir): os.remove(logdir)
    create_timed_rotating_log(logdir, "clean")

logger = logging.getLogger("default")
logger_codes = logging.getLogger("codes")
logger_clean = logging.getLogger("clean")
#logger_clean.info = logger_clean.info

from zhipuai import ZhipuAI

CLIENT = ZhipuAI(
    api_key="6938cf4636f939c984a2825d527ad273.oM7nYeOxh5Adkc6k"
)

import random
def get_client():
    #idx = random.randint(0,100) % 3
    #if idx <= 1: return CLIENT
    #else: return CLIENT2
    return CLIENT

MODEL_CODE="glm-4-0520"
MODEL="glm-4-0520"
#MODEL="glm-4-air"
tools = [{"type":"web_search", "web_search":{"enable": False}}]
FUNC2PROMPT = {}
DIR_NAME = "./prompt_apis"
for file in os.listdir(DIR_NAME):
    idx, func = file.split('_', 1)
    func = func.strip().lstrip()
    prompt = open(f"{DIR_NAME}/{file}", encoding='utf-8').read().strip().lstrip()
    api_desc, code_eg = prompt.split('='*10)
    fname = prompt.split('\n')[0].strip().lstrip().strip(',')
    FUNC2PROMPT[func] = (prompt, fname, api_desc, code_eg)


def gen_code(messages, run_tag):
    logger_codes.info(f"gen_code call tag={run_tag} message={messages}")
    response = get_client().chat.completions.create(model=MODEL_CODE,messages=messages, temperature=0.01, tools=tools)
    text = response.choices[0].message.content
    codes = re.findall(r"```python([\s\S]+?)```", text)
    logger_codes.info(f"gen_code ret tag={run_tag} text={text}")
    return text, codes

NEW_CODE_HINT = """根据上文和运行输出判断, 对于分步问题'{sub_q}':
- 如果上文已经足够得到'分步问题'的答案，就不生成代码，直接回答分步问题, 回答格式为"通过条件XXX为YYY查询得到ZZZ是KKK, 通过条件A为B查询得到C是D, ...", 如果有多个输出不要省略{tbl_output_hint}
- 注意, 仅根据代码查询输出的内容进行回答, 不使用你的通用知识做任何推断猜测
- 否则, 继续生成代码进行查询"""

CODE_ERR_HINT_PROMPT = """错误解决思路:
- 如果是'没有查询到数据'可以尝试重写代码, 切换查询字段(如果get接口支持), 比如对'公司名称'查询没有，可以尝试对'公司简称'进行查询
- 如果是'没有查询到数据'可以尝试重写代码, 对查询query关键词进行修复纠错后再查询，比如将"北京"修复为"北京市"，比如"2020年06月06日"修复为"2020年6月6日", 比如"上上海海行星有有限限公公司司"修复为"上海行星有限公司", 比如按常识"温洲"并不存在, 应修复为"温州"
- 如果反复'没有查询到数据'并且纠错无效, 直接返回: ##dead_end没有查询到数据
"""
full = open('./prompt_refers', encoding='utf-8').read()
patn_fix = r"###start###(.+?)\n([\s\S]+?)\n###"
func2fix = {}
for func, prompt in re.findall(patn_fix, full):
    func2fix[func] = prompt
CODE_ERR_HINT_PROMPT2 = """错误解决思路:
- 如果是'没有查询到数据', 可能是查询词需要纠错改写, 可以尝试重写代码, 参考以下例子改写查询词格式(注意不要变更查询对象!):{refers}
"""###dead_end 没有查询到数据
#- 如果多次纠错改写查询词格式，还是查询不到, 直接返回: ###dead_end 没有查询到数据
def func_specific_error_prompt(func):
    refers = func2fix[func]
    return CODE_ERR_HINT_PROMPT2.format(refers=refers)

def run_codeact_step(user_query, step_query, input_hint, output_hint, func, cur_answer, code_context_history=[], max_depth=6, max_retry=4):
    sys_prompt, user_prompt = open('prompt_code_act').read().strip().lstrip().split('='*10)
    func = func.strip().lstrip().lower()
    prompt, fname, api_desc, code_eg = FUNC2PROMPT[func]

    sys_message = sys_prompt.format(api_desc=api_desc, code_example=code_eg, func=func)
    user_message = user_prompt.format(sub_query=step_query, input_help=input_hint, output_help=output_hint)

    logger.info(f"run_steps called q={user_query} stepq={step_query} func={func}, ctxlen={len(code_context_history)}, ctx={code_context_history}")
    messages = code_context_history + \
    [{"role":"system", "content": sys_message}, {"role":"user", "content": user_message}]
    refer_kvs = []
    accumulated_codes = ''
    refers_params = func2fix[func]
    tbl_output_hint_list = [x for x in refers_params.split('\n') if '输出注意' in x]
    tbl_output_hint = '\n' + '\n'.join(tbl_output_hint_list) if len(tbl_output_hint_list) > 0 else ''

    gen_text = ''
    any_successful_get = False
    for idx_depth in range(max_depth):
        run_tag = f"proceed_{idx_depth}"
        retry_messages = messages.copy()
        for idx_retry in range(max_retry):
            text, codes = gen_code(retry_messages, run_tag)
            if len(codes) == 0: #codeAct done
                #只保留最后一次正确的retry代码
                #logger_codes.info(f"q={user_query} 完成step={step_query} text={text} messages={messages[len(code_context_history):]}")
                logger_codes.info(f"q={user_query} 完成step={step_query} text={text}")
                #text是生成的无代码回答
                NOT_GOOD_KW = ["无法通过", "没有", "没有"]
                if any([x in text for x in NOT_GOOD_KW]) and ('get_' in text):
                    logger_codes.info(f"q={user_query} 完成step={step_query} 启发式无法获取")
                    return False, text, messages[len(code_context_history):]
                    
                any_progress, progress_text = is_any_progress(step_query, cur_answer, text, tbl_output_hint)
                #如果没有progress, 检查下是否是上一步导致的, 即last step可能本来是有progress的
                if not any_progress and len(gen_text) > 0:
                    any_progress_b, progress_text_b = is_any_progress(step_query, cur_answer, gen_text, tbl_output_hint)
                    return any_progress_b, gen_text, messages[len(code_context_history):], refer_kvs
                else:
                    return any_progress, text, messages[len(code_context_history):], refer_kvs
                #is_done, sub_todo, cur_answer = is_done_func(step_query, [[text]])
                #if is_done:
                #else:
                #    #就再来一把:
                #    messages += [{"role":"assistant", "content": text}, {"role":"user", "content": sub_todo}]
                #    logger_codes.info(f"step={step_query} text={text} add query={sub_todo}")
                #    break
                
            else:
                the_code = '\n'.join(codes)
                run_code_full = f'{accumulated_codes}\n{the_code}'
                if is_good_code_hueristic(run_code_full):
                    run_success, gen_text, error_info, kv_infos = run_code(user_query, run_code_full, run_tag)

                    if run_success:
                        #保护一下, 如果查到的, 但是查询词为空
                        #或者查询词(指value)不在prompt里面, 但是在给的例子里面, 说明可能被带偏了，直接没用查询到数据吧
                        if len(kv_infos) > 0:
                            any_successful_get = True
                        hit_values = []
                        hit_goods = []
                        for k,params in kv_infos:
                            if not k.startswith('get'): continue
                            value = params[1]
                            hit_values.append(value)
                            hit_goods.append(value not in user_message and value in refers_params) #不在prompt 但是在入参例子里面
                        if not any_successful_get or any(hit_goods):
                            logger_clean.warn(f"q={user_query} stepq={step_query} 通过假数据查询了api却命中={kv_infos} {hit_values} {hit_goods}")
                            return False, "##dead_end没有查询到数据", messages[len(code_context_history):]
                        
                    if run_success: #执行成功，下一轮
                        messages += [{"role":"assistant", "content": text}, {"role":"user", "content": f"代码执行结果:{gen_text}\n{NEW_CODE_HINT.format(sub_q=step_query, tbl_output_hint=tbl_output_hint)}"}]
                        accumulated_codes += f'\n{the_code}'
                        refer_kvs.append(kv_infos)
                        break # break retry loops
                    elif "##dead_end没有查询到数据" in error_info:
                        logger_codes.warn(f"q={user_query} stepq={step_query} 没有查询到数据 {idx_depth}{idx_retry} error_info={error_info}")
                        return False, "##dead_end没有查询到数据", messages[len(code_context_history):]
                    else:
                        logger_clean.warn(f"retry_count {idx_depth} {idx_retry}")
                        run_tag = f"retry_{idx_depth}_{idx_retry}"
                        assert type(error_info) == str, error_info
                        #error_info += CODE_ERR_HINT_PROMPT
                        error_info += func_specific_error_prompt(func)
                        retry_messages += [{"role":"assistant", "content": text}, {"role":"user", "content": error_info}]
                else:
                    logger_codes.warn(f"q={user_query} stepq={step_query} bad hueristic code full={run_code_full}")
                    logger_clean.warn(f"retry_count {idx_depth} {idx_retry}")
                    run_tag = f"retry_{idx_depth}_{idx_retry}"
                    assert type(error_info) == str, error_info
                    #error_info += CODE_ERR_HINT_PROMPT
                    error_info += func_specific_error_prompt(func)
                    retry_messages += [{"role":"assistant", "content": text}, {"role":"user", "content": error_info}]
                if idx_retry < max_retry - 1: continue #retry generate code

                logger.warn(f"q={user_query} stepq={step_query} 代码生成异常 {idx_depth}{idx_retry} func={func} messages={retry_messages}")
                return False, "代码生成异常, 未完全查询到答案", messages[len(code_context_history):]

    logger.warn(f"q={user_query} stepq={step_query} 迭代轮次{max_depth}内 未完全找到答案 messages={messages}")
    return False, "未完全查询到答案", messages[len(code_context_history):] #超过code-act迭代轮数



dummy_code = """
#header
"""

def proc_refer_logs(rawlog):
    refer_lines = [x.strip().lstrip()[len('参考数据格式'):] for x in rawlog.split('\n') if '参考数据格式' in x]
    refer_infos = []
    for line in refer_lines:
        js = json.loads(line)
        api, cond = js
        params = []
        for k,v in cond.items():
            params.append(k)
            params.append(v)
        refer_infos.append([api, params])
    return refer_infos

import pickle
import re
patn_ex = r'File "<string>".+line (\d+).+'
import re
def extract_stack_info(codes):
    st = traceback.format_exc()
    pickle.dump(st, open('st.pkl', 'wb'))
    frames = st.strip().lstrip().split('\n')
    code_frames_idx = [idx for idx,sline in enumerate(frames) if 'exec(uq, globals())' in sline]
    if len(code_frames_idx) == 1 and code_frames_idx[0] < len(frames) - 1:
        kidx = code_frames_idx[0]
        usefull_frames = frames[kidx + 1:]
        line_no_frame = usefull_frames[0]
        line_no_strs = re.findall(patn_ex, line_no_frame)
        if len(line_no_strs) == 1:
            line_no = int(line_no_strs[0])
            code_line = codes.split('\n')[line_no - 1]
            usefull_frames[0]+= f' {code_line}'
            nst = '\n'.join(usefull_frames)
            logger_codes.warn(f"reformat frame, addcodeln={line_no} addinfo={code_line} to st={nst}")
            return nst
    return st

def pre_process_globals(globals):
    gdict = globals.copy()
    for k,v in gdict.items():
        if k in FUNC2PROMPT:
            gdict[k] = deco_get(v)
    return gdict
     

def run_code(user_query, code_raw, run_tag):
    f = StringIO()
    ferr = StringIO()
    try:
        with redirect_stdout(f):
            uq = f"\n{dummy_code}\n" + code_raw
            exec(uq, pre_process_globals(globals()))
        raw_results = f.getvalue()
        refer_infos = proc_refer_logs(raw_results)
        results = '\n'.join([x for x in raw_results.split('\n') if '参考数据格式' not in x])
        slog = raw_results.replace('\n', '\\n')
        logger_codes.info(f"code_exec_success q={user_query} run_tag={run_tag} s={slog} results={results} refer_infos={refer_infos}")
        logger.info(f"code_exec_success q={user_query} run_tag={run_tag} s={slog} results={results} refer_infos={refer_infos}")
        #if '##没查询到数据' not in results:
        #    logger_clean.info(f"get_run_code_kvs={refer_infos}")
        return '##没查询到数据' not in results, results, '',refer_infos
    except Exception as ex:
        raw_results = f.getvalue()
        refer_infos = proc_refer_logs(raw_results)
        st = extract_stack_info(uq)
        error_info = str(ex) if '没查询到数据' in str(ex) else st
        error_message =  f"代码运行错误, 提示:{error_info} {refer_infos}"
        logger_codes.warn(f"code exec run_tag={run_tag} error={error_message} ")
        logger.warn(f"code exec run_tag={run_tag} error={error_message} ")
        return False,raw_results, error_message, []


BAD_PATTERN = []
def is_good_code_hueristic(code_raw):
    """
    funcs_names = [x.strip().lstrip() for x in tbl_funcs.strip().lstrip().split('/')]
    if not any([func_name in code_raw for func_name in funcs_names]):
        logger_codes.warn("bad code generated: not any valid func calls in")
        return False
    """
    for bad_pattn in BAD_PATTERN:
        if bad_pattn in code_raw:
            logger_codes.warn(f"bad code generated: bad pattn={bad_pattn}")
            return False
    return 'get_' in code_raw

import re
#patn = r"是否需要查询该接口.+?([是否])\n#.+?提供了查询所需的输入字段(.+?)\n#需要查询的输出字段(.+?)\n"
parse_patn1 = r"是否需要查询该接口.+?([是否])"
parse_patn2 = r"提供了查询所需的输入字段(.+)\n#需要查询的输出字段(.+)"
def parse_plan(raw):
    mts_need = re.findall(parse_patn1, raw)
    if len(mts_need) != 1: return False, False, '', ''
    is_api_need_str = mts_need[0]
    is_api_need = '是' in is_api_need_str
    if not is_api_need:
        return False, False, '', ''
    
    mts_api_info = re.findall(parse_patn2, raw)
    if len(mts_api_info) != 1: return is_api_need, False, raw, raw
    is_args_rdy_str, output_str = mts_api_info[0]
    args_rdy_cols = re.split('[,，]', is_args_rdy_str, maxsplit=1)
    if len(args_rdy_cols) == 2 and '是' in args_rdy_cols[0]:
        is_args_rdy = True
        input_str = ','.join(args_rdy_cols[1:])
    else:
        is_args_rdy = False
        input_str = ''

    #return is_api_need, is_args_rdy, f'查询输入:{input_str}', f'要查询的输出字段{output_str}'
    return is_api_need, is_args_rdy, input_str, output_str

def run_planing(user_query):
    psys = """{api_desc}
    你在查询多个信息接口来回答'用户提问', 以上'{api_fname}'是其中之一,
    请问某一步查询中, 是否会用到该接口查询部分信息，请按以下格式回答：
    #是否需要查询该接口: 是/否
    #提问中是否提供了查询所需的输入字段: 是/否, 如果是 提供查询的字段 '字段名'='查询值'
    #需要查询的输出字段: ...
    #end(不做其他解释)"""
    user = user_query

    api_routes_messages = []
    for func, items in FUNC2PROMPT.items():
        prompt, fname, api_desc, code_eg = items
        messages = [{"role":"system","content": psys.format(api_desc=api_desc, api_fname=fname)},
                    {"role":"user", "content": f"用户提问:\n {user}"}]
        
        response = get_client().chat.completions.create(model=MODEL,messages=messages, temperature=0.01, tools=tools)
        text = response.choices[0].message.content
        is_api, is_args, input_hint, output_hint = parse_plan(text)
        api_routes_messages.append([is_api, is_args, input_hint, output_hint, func, messages, text])
    return api_routes_messages

def get_sub_query(query, plans):
    user = f"""在原用户提问'{query}'中，该查询能解决哪些子问题, 一句话给出全部的子问题(沿用原提问的表述方式, 不做改写, 子问题应该是原问题的一部分), 格式如下:
#该查询能解决的所有子问题: ...
#end(不做其他解释, 只有一个子问题)"""
    cur_plans = []
    backup_plans = []
    any_api_cnt_plan = False
    for is_api, is_args, input_hint, output_hint, func, messages, text in plans:
        if is_api and is_args:
            mess_new = messages + [{"role":"assistant","content": text}, {"role":"user","content": user}]
            response = get_client().chat.completions.create(model=MODEL_CODE,messages=mess_new, temperature=0.01, tools=tools)
            ntext = response.choices[0].message.content
            sub_query = ntext[len("#该查询能解决的所有子问题:"):-len("#end")]
            if ('api' in sub_query.lower() or 'ＡＰＩ' in sub_query) and func != 'get_api_call_cnt':
                logger_clean.warn(f"sub={sub_query}, with api cnt, but func={func}, skip")
                continue
            cur_plans.append([input_hint.strip(), output_hint.strip(), func, sub_query.strip(), text])
        if is_api and not is_args:
            if func == 'get_api_call_cnt': any_api_cnt_plan = True
            else:
                backup_plans.append([input_hint.strip(), output_hint.strip(), func, '', text])
            
    
    return cur_plans, backup_plans, any_api_cnt_plan

def is_any_progress(question, cur_answer, text, output_hint=""):
    sysp, userp = open('./prompt_any_progress').read().split('='*10)
    sysp, userp = [x.lstrip().strip() for x in [sysp, userp]]

    messages = [{"role":"system", 'content':sysp}, {"role":"user", 'content':userp.format(question=question, answer=cur_answer, answer_add=text, output_hint=output_hint).lstrip()}]
    response = get_client().chat.completions.create(model=MODEL_CODE,messages=messages, temperature=0.01, tools=tools)
    text = response.choices[0].message.content
    
    idx_find = text.find("##回答B是否补充了新的信息")
    assert idx_find >= 0, text
    text = text[idx_find:].lstrip().strip()
    text_rows = text.strip().lstrip().split('\n', 1)
    assert idx_find >= 0, text
    is_done = '是' in text_rows[0][len('##回答B是否补充了新的信息'):]
    sub_todo = ''
    if is_done:
        assert len(text_rows) >= 2
        idx = text_rows[1].find("提取出新的信息")
        assert idx >=0, text_rows[1]
        sub_todo = text_rows[1][idx + len("提取出新的信息"):]
    
    logger.info(f"is_any_progress question={question}, info={cur_answer, text} res={is_done, text_rows, sub_todo}")
    return is_done, sub_todo

def rephrase_part_ans(question, sub_answers):
    sys = """例子1(不输出无法回答/无法查询的部分问题)
    ##问题A: 橙光文具的子公司中, 投资金额最高的是哪家?
    ##查询结果: `` 
    橙光文具的子公司中, 投资金额最高的是哪家?
    由于无法直接查询到橙光文具的子公司, 我们无法回答这一部分的分步问题。以下是针对已查询到的信息回答：
    通过'公司简称'='橙光文具'得到该公司名称为'上海晨光文具测试股份有限公司'
    该公司涉及案件的审理法院包括代字为沪01,沪02,沪03的法院
    ```
    ##部分答案: '橙光文具'是'公司简称', 公司名称为'上海晨光文具测试股份有限公司', 该公司涉及审理法院代字包括沪01,沪02,沪03

    例子2(无法查到返回空, 不输出无法回答的部分问题)
    ##问题A: 公司A的法人代表是谁?
    ##查询结果: `` 
    无法通过get_company_register获取到相关信息
    ```
    ##部分答案: 

    例子3(按提问顺序, 中间信息完整的回答)
    ##问题A: F124A公司是否涉案, 涉案金额最高的被告是谁?
    ##查询结果: ```(省略)```
    ##部分答案: 公司代码为F124A的公司名称为黄光文具有限公司, '关联公司'为黄光文具有限公司的案件有3起，说明该公司是涉案, 涉案金额最高的案号为'(2020)沪01民1号', 被告为陈默默


    参考以上例子, 我正在回答'问题A', 你是我的问答助手, 根据'问题A'和我提供的'查询结果', 提取并输出已经可以回答的'部分答案', 注意:
    - 尽量沿用问题Q的表述方式和提问顺序, 并且包含'查询结果'中提供的查询路径，比如'通过字段A=B查询得到字段C=D'
    - 不一定能回答'问题A'中所有问题, 仅提取和输出能回答的部分或者提供了扩展信息帮助下一步查询
    - 所有的回答语句都必须包含主语, 做到self-explain，比如具体是谁的AA字段是BB
    - 没有查询到/无法回答的部分问题不输出或解释, 后续会用继续用其他方法查询，尽量精简
    - 输出格式, ##部分答案: ..."""

    user = """##问题A:{question}
    ##查询结果: ```
    {answers_concat}
    ```
    ##部分答案:
    """
    answers_concat = ','.join([x for depth in sub_answers for x in depth])
    messages = [{"role":"system", 'content':sys}, {"role":"user", 'content':user.format(question=question, answers_concat=answers_concat)}]
    response = get_client().chat.completions.create(model=MODEL_CODE,messages=messages, temperature=0.01, tools=tools)
    text = response.choices[0].message.content
    return text


def is_done_func2(question, sub_answers, prefix=''):
    #return is_done, sub_todo
    if len(sub_answers) == 0:
        return False, question, ''

    cur_answer = rephrase_part_ans(question, sub_answers)
    sysp, userp = open('./prompt_is_done').read().split('='*10)
    sysp, userp = [x.lstrip().strip() for x in [sysp, userp]]

    cur_answer = prefix + cur_answer #避免上下文断裂

    messages = [{"role":"system", 'content':sysp}, {"role":"user", 'content':userp.format(question=question, answer=cur_answer)}]
    response = get_client().chat.completions.create(model=MODEL_CODE,messages=messages, temperature=0.01, tools=tools)
    text = response.choices[0].message.content
    
    idx_find = text.index("回答A是否完整")
    text = text[idx_find:].lstrip().strip()
    text_rows = text.strip().lstrip().split('\n')
    assert idx_find >= 0, text_rows
    is_done = '是' in text_rows[0][len('##回答A是否完整'):]
    sub_todo = ''
    if not is_done:
        assert len(text_rows) >= 2
        assert '##如果不完整, 给出未回答的子问题' in text_rows[1]
        sub_todo = text_rows[1][len('##如果不完整, 给出未回答的子问题:'):]
    
    logger.info(f"is_done question={question}, messages={messages} res={is_done, sub_todo}")
    return is_done, sub_todo, cur_answer


def rephrase(question, answer):
    sys_prompt = """
    例子1:
    ##问题: 我想了解上海妙可蓝多食品科技股份有限公司的法人与总经理姓名是否一致。
    ##查询结果: 根据公司名称=上海妙可蓝多食品科技股份有限公司'查询得到法人代表为柴琇, 查询得到总经理为柴琇，两者一致
    ##关键词: 公司名称, 上海妙可蓝多食品科技股份有限公司, 法人代表, 柴琇, 总经理, 柴琇, 一致
    ##最终答案: 经查询，上海妙可蓝多食品科技股份有限公司的法人代表为柴琇，总经理为柴琇，与总经理姓名一致。

    例子2:
    ##问题: 北京金杜律师事务所服务已上市公司的数量是多少家
    ##查询结果: 根据律师事务所名称=北京金杜律师事务所查询到"服务已上市公司"为68
    ##关键词: 律师事务所名称, 北京金杜律师事务所, 服务已上市公司, 68家
    ##最终答案: 经查询, 律师事务所名称为北京金杜律师事务所服务已上市的数量是68家

    例子3:
    ##问题: (2020)新2122民初1105号案件中，审理当天审理法院与原告的律师事务所所在城市的最高度相差多少度?本题使用的API个数为?最小调用次数为多少次?
    ##查询结果: 根据案号'(2020)新2122民初1105号'查询得到'法院代号'新2122'得到法院'鄯善县人民法院', '原告律师事务所'='浙江百方律师事务所','审理日期'='2020年11月6日', 法院地址'新疆吐鲁番市鄯善县新城东路1208号', 律师事务所地址'环城东路251号天洁大厦17层', 前者省市'新疆维吾尔自治区, 吐鲁番市', 后者'浙江省, 绍兴市', 得到温度3度/22度，差值19度，本题使用的API个数为6个，最小调用次数为8次
    ##关键词: (2020)新2122民初1105号, 浙江百方律师事务所, 鄯善县人民法院, 2020年11月6日, 环城东路251号天洁大厦17层, 新疆吐鲁番市鄯善县新城东路1208号, 浙江省, 绍兴市, 新疆维吾尔自治区, 吐鲁番市, 3度, 22度, 19度, 6个, 8次
    ##最终答案: 经查询，(2020)新2122民初1105号的审理日期为2020年11月6日，该案件的原告律师事务所是浙江百方律师事务所，审理法院是鄯善县人民法院，原告律师事务所地址为环城东路251号天洁大厦17层，审理法院地址为新疆吐鲁番市鄯善县新城东路1208号，原告律师事务所地址所在省份为浙江省，城市为绍兴市，审理法院地址所在省份为新疆维吾尔自治区，城市为吐鲁番市，最低温度分别为3度及22度，最低温度相差19度，本题使用的API个数为6个，最小调用次数为8次。


    你是问答助手，参考以上例子, 根据'问题'和提供的'查询结果'，提取问答的'关键词'，并提供包含所有关键词的'最终答案'，注意:
    - '关键词'提取自'问题'和'查询结果', 包括问题涉及的核心判断、名字、查询用的字段、量纲(家/次/个/元/万元等等...)
    - '关键词'尽可能全, 同一个概念有多个表述方式时(比如来自问题和来自查询), 都要包含
    - '最终答案'尽可能完整, 不要省略关键词或合并，涉及输出多个对象，按列举格式"A的情况, B的情况, C的情况....."
    - 如果查询结果金额数量没有量纲, 比如123.00，关键词和最终答案上请加上量纲"元", 比如123.00元
    - 输出格式如下:
    ##关键词: 关键词1, 关键词2, ...
    ##最终答案: ....
    """

    user = f"""##问题: {question}
    ##查询结果: {answer}
    """
    messages = [{"role":"system", "content": sys_prompt}, {"role":"user", "content": user}]
    response = get_client().chat.completions.create(model='glm-4-0520',messages=messages, temperature=0.01)
    text = response.choices[0].message.content
    return text

XZGXF_KEYS = ["消费", "高消", "限制"]
def is_good_plan(sub_query, func, depth_idx, depth_layer_funcs):
    if 'xzgxf' in func and not any([key in sub_query for key in XZGXF_KEYS]):
        return False

    #if depth_idx >= 1:
    #    return func not in depth_layer_funcs[depth_idx - 1]
    return True


def get_inter_query(cur_ans, sub_todo, plan, args_ready=False):
    if args_ready:
        input_hint, output_hint, func, sub_query, text = plan
    else:
        input_hint, output_hint, func = plan[:3]
    output_hint = re.findall(r"([\u4e00-\u9fa5]+)", output_hint)[0]
    sys = """
    按以下例子格式回答问题，生成查询子问题:

    例子1
    问题: (2022)沪123号案件审理当天最高温度多少?
    已知查询'最高温度'所需的输入字段: 省份, 城市, 日期
    所以为了回答问题, 不能直接查询'最高温度', 而是先查询子问题: (2022)沪123号案件审理的省份, 城市和日期是什么?

    例子2
    问题: A公司涉及的案件中, 受理最多的法院的法院地址在哪？
    已知查询'法院地址'所需的输入字段: 法院名称
    所以为了回答问题, 不能直接查询'法院地址', 而是先查询子问题: A公司涉及的案件中, 受理最多的法院的法院名称是什么?

    例子3
    问题: 被告有橙光文具的案件中, 涉案金额最高的是多少?
    已知查询'涉案金额'所需的输入字段: 关联公司(又名:公司名称)
    所以为了回答问题, 不能直接查询'涉案金额', 而是先查询子问题: 橙光文具(可能是简称)作为案件关联公司, 它的公司名称是什么?
    """
    prompt, fname, api_desc, code_eg = FUNC2PROMPT[func]
    inter_query_key = [x for x in api_desc.split('\n') if '输入字段' in x][0][len('输入字段:'):]
    if inter_query_key in {"关联公司", "限制高消费企业名称"}:
        inter_query_key += "(又名:公司名称)"
    
    user = f"""
    问题A：{sub_todo}
    已知查询'{output_hint}'所需的输入字段: {inter_query_key}
    所以为了回答问题A, 不能直接查询'{output_hint}', 而是先查询子问题:
    """

    MODEL_CODE="glm-4-0520"
    messages = [{"role":"system", "content": sys}, {"role":"user", "content": user}]
    response = get_client().chat.completions.create(model='glm-4-0520',messages=messages, temperature=0.01)
    text = response.choices[0].message.content
    logger.info(f"generate inter_query={text} user={user}")

    #如果inter_query比原query长很多，那就有问题:


    return text

def pipeline_0711(user_query):
    logger_clean.info(f'start query={user_query}')
    if '起诉状' in user_query:
        return False, "目前不解决起诉状问题", "目前不解决起诉状问题", [[],[],[],[]]

    MAX_DEPTH = 10
    depth_answers = []
    depth_queries = []
    depth_plans = []
    depth_plans_result = []
    depth_code_context = []
    depth_plans_all = []
    depth_layer_funcs = []
    depth_inter_sub_queries = {}
    depth_kv_refers = []

    plan_results_cache = {}

    for depth_idx in range(MAX_DEPTH):
        last_layer_funcs = set()
        if depth_idx - 1 in depth_inter_sub_queries:
            is_done, sub_todo, cur_answer = False, ','.join(depth_inter_sub_queries[depth_idx-1]), cur_answer
        else:
            is_done, sub_todo, cur_answer = is_done_func2(user_query, depth_answers)
            logger_clean.info(f'is_done={is_done} question={user_query} cur_answer={cur_answer} todo={sub_todo}')
        if is_done: break
        
        user_query_context = f"{cur_answer}, {sub_todo}"
        plans = run_planing(user_query_context)
        cur_plans, backup_plans, any_api_cnt_plan = get_sub_query(sub_todo, plans)
        
        logger_clean.info(f'depth={depth_idx} todo={sub_todo}, cur_ans={cur_answer}, len={len(cur_plans)} any_api_cnt_plan={any_api_cnt_plan}')
        depth_queries.append([user_query_context, sub_todo])
        depth_plans.append(cur_plans)
        depth_plans_all.append(plans)

        results = []
        if len(cur_plans) == 0 and len(backup_plans) == 0 and (any_api_cnt_plan or 'API' in user_query): #只剩api count任务, 添加这部分结果
            result, api_seq = get_api_call_cnt(depth_kv_refers)
            logger_clean.info(f'    depth={depth_idx} func="api_cnt_plan", result={result}')
            results.append(result)
            depth_answers.append(results)
            depth_plans_result.append(results)
            depth_code_context.append(api_seq)
            continue

        cur_plans_no_skip = []
        for input_hint, output_hint, func, sub_query, text in cur_plans:
            if not is_good_plan(sub_query, func, depth_idx, depth_layer_funcs):
                logger_clean.info(f'    depth={depth_idx} func={func}, skipped, subq={sub_query}')
                continue

            plan_cache_key = f'{func}-{input_hint.strip().lstrip()}-{output_hint.strip().lstrip()}'
            if plan_cache_key in plan_results_cache:
                #其实可以skip
                logger_clean.info(f'    depth={depth_idx} func={func}, skipped, subq={sub_query}, cached={plan_cache_key}')
                continue
                #ret = plan_results_cache[plan_cache_key]
            else:
                logger_clean.info(f'    depth={depth_idx} func={func}, subq={sub_query} input_hint={input_hint} output_hint={output_hint}')
                ret = run_codeact_step(user_query, sub_query, input_hint, output_hint, func, cur_answer, []) #do not share context for now
                plan_results_cache[plan_cache_key] = ret
                logger_clean.info(f'    ret[:2]={ret[:2]}')

            if ret[0]: #success show kvinfo
                logger_clean.info(f"    related_get_run_code_kvs={ret[-1]}")

            results.append(ret)
            cur_plans_no_skip.append([input_hint, output_hint, func, sub_query, text])
        
        depth_plans_result.append(results)
        any_sub_done = any([x[0] for x in results])
    
        if not any_sub_done:
            inter_sub_queries = []
            if len(cur_plans) == 0:
                if len(backup_plans) != 0:
                    for backup_plan in backup_plans:
                        new_q = get_inter_query(cur_answer, sub_todo, backup_plan, args_ready=False)
                        if new_q: inter_sub_queries.append(new_q)
            else:
                for cur_plan in cur_plans:
                    new_q = get_inter_query(cur_answer, sub_todo, cur_plan, args_ready=True)
                    if new_q: inter_sub_queries.append(new_q)
            
            if len(inter_sub_queries) == 0:
                break
            else:
                logger_clean.info(f'    depth={depth_idx} inter_queries={inter_sub_queries}')
                depth_inter_sub_queries[depth_idx] = inter_sub_queries
                depth_code_context.append([])
                depth_answers.append([])
                depth_layer_funcs.append(last_layer_funcs)
                continue
        
        answers = []
        code_context = []
        for ret, plan in zip(results, cur_plans_no_skip):
            if len(ret) == 3:
                kv_refer = []
                is_sub_done, sub_answer, sub_code_context = ret
            else:
                is_sub_done, sub_answer, sub_code_context, kv_refer = ret
            #sub_code_context = [system, user] if not is_sub_done
            #sub_code_context = [system, (user, code)*N, user(result)] if is_sub_done
            if is_sub_done:
                answers.append(sub_answer)
                #take (user, code)*N + user+sub_answer
                take_context = [x for x in sub_code_context if x['role'] != 'system']
                take_context[-1]['content'] += f'\n{sub_answer}'
                code_context.append(take_context)
                input_hint, output_hint, func, sub_query, text = plan
                last_layer_funcs.add(func)
                depth_kv_refers.append(kv_refer)
        
        depth_code_context.append(code_context)
        depth_answers.append(answers)
        depth_layer_funcs.append(last_layer_funcs)
        logger_clean.info(f'depth={depth_idx} done, {last_layer_funcs}')
    
    logger_clean.info(f"q={user_query} is_done={is_done} raw_answer={cur_answer}")
    rephrase_ans = rephrase(user_query, cur_answer)
    debug_info = [depth_queries, depth_answers, depth_plans, depth_code_context, depth_plans_all, depth_kv_refers]
    logger_clean.info(f"q={user_query} is_done={is_done} raw_answer={cur_answer} rephrase_ans={rephrase_ans}")
    return is_done, cur_answer, rephrase_ans, debug_info, depth_kv_refers

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        user_query = sys.argv[1]
    else:
        raise ValueError('Please provide user query.')
    print(pipeline_0711(user_query))