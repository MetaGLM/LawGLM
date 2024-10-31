from typing import Iterable
import jsonlines
import importlib
import re 
from pathlib import Path
import json
import logging
import time
from langchain_core.prompts import PromptTemplate
import pandas as pd
import io
import traceback
import subprocess
import threading
import os
from tools.tool_correction_info import *

def clean_res(res):
    res_list = res.split('\n')
    no_add_item = ['pandas.core.frame.DataFrame', 'RangeIndex:','dtypes:','memory usage', '详细信息：None']
    new_list = []
    for item in res_list:
        add  = True 
        for no_add in no_add_item:
            if no_add in item:
                add = False 
                break
        if "non-null" in item.lower():
            item = item.replace("\t", " ")
            item = item.replace("Non-Null", "")
            item = item.replace("non-null", "")
        if add:
            new_list.append(item)
    return '\n'.join(new_list)


def run_code_in_file(py_code, output_file, code_file):
    """
    将给定的代码保存到文件中，并在子进程中运行该文件。
    :param py_code: 字符串形式的Python代码
    :param output_file: 用于保存输出的文件名
    :param code_file: 用于保存代码的文件名
    """
    try:
        # 将代码与必要的导入语句合并保存到文件中
        with open(code_file, 'w') as f:
            f.write('import sys\n')
            f.write('sys.path.append("/public/zzy/competition/coder")\n')  # 替换为实际路径
            f.write(py_code)

        # 获取当前工作目录
        current_directory = os.getcwd()

        # 在子进程中运行代码文件，并将输出重定向到文件中
        result = subprocess.run(['/root/anaconda/envs/competition/bin/python', code_file], capture_output=True, text=True, cwd=current_directory)
        with open(output_file, 'w') as f:
            f.write(clean_res(result.stdout))
            if result.stderr:
                f.write(clean_res(result.stderr))
    except Exception:
        # 捕获详细错误信息
        error_message = traceback.format_exc()
        with open(output_file, 'w') as f:
            f.write("代码执行错误" + error_message)
    finally:
        # 删除临时代码文件
        if os.path.exists(code_file):
            os.remove(code_file)

def python_inter(py_code, save_path):
    """
    该函数的主要作用是对iquery数据库中各张数据表进行查询和处理，并获取最终查询或处理结果。
    :param py_code: 字符串形式的Python代码，此代码用于执行对iquery数据库中各张数据表进行操作
    :return：返回代码运行的最终结果，包括代码执行时的控制台输出
    """
    # 记录函数开始执行时，全局作用域内的变量名
    global_vars_before = set(globals().keys())
    
    # 定义文件名
    output_file = save_path
    code_file = save_path.replace('.txt', '.py')
    
    # 创建并启动线程来运行代码
    thread = threading.Thread(target=run_code_in_file, args=(py_code, output_file, code_file))
    thread.start()
    thread.join()

    # 读取文件中的输出内容
    with open(output_file, 'r') as f:
        output = f.read()

    # 删除临时输出文件
    if os.path.exists(output_file):
        os.remove(output_file)
    return output


def parse_json_to_df(json_data):
    if isinstance(json_data, dict):
        return pd.DataFrame([json_data])
    elif isinstance(json_data, list):
        return pd.DataFrame(json_data)
    else:
        return pd.DataFrame()
    

# 定义一个函数read_jsonl，用于读取jsonl文件
def read_jsonl(path):
    # 初始化一个空列表，用于存储读取到的内容
    content = []
    # 使用jsonlines库打开jsonl文件，并设置为只读模式
    with jsonlines.open(path, "r") as json_file:
        # 遍历json文件的每一行，将其转换为字典类型
        for obj in json_file.iter(type=dict, skip_invalid=True):
            # 将每一行添加到content列表中
            content.append(obj)
    # 返回content列表
    return content


def save_answers(
        queries: Iterable, results: Iterable, result_file: str = "./data/results/伍柒_result.json",
):
    answers = []
    for query, result in zip(queries, results):
        answers.append(
            {
                "id": query["id"],
                "question": query["question"],
                "answer": result
            }
        )

    # use jsonlines to save the answers
    def write_jsonl(path, content):
        with jsonlines.open(path, "w") as json_file:
            json_file.write_all(content)

    # 保存答案 result_file 指定位置
    write_jsonl(result_file, answers)


def read_txt_file_to_list(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 使用列表推导式将每一行转换为列表的元素
            data_list = [line.strip() for line in file]
            data_list = [ele for ele in data_list if ele != '']
        return data_list
    except FileNotFoundError as e:
        print(f"File {file_path} not found.")
        raise e


def convert_to_float(s):
    if s is None:
        return 0

    # 使用正则表达式将字符串中的数字和中文符号替换为英文符号
    s = s.replace("亿", "e8").replace("万", "e4")

    try:
        # 使用float函数将字符串转换为浮点数
        result = float(s)
    except Exception as e:
        result = 0
    return result


def convert_to_str(f):
    if f > 1e8:
        f = f / 1e8
        return f'{round(f, 2):.2f}' + '亿'
    if f > 1e4:
        f = f / 1e4
        return f'{round(f, 2):.2f}' + '万'
    return f'{round(f, 2):.2f}'

def compare_rank_name(d1, d2):
    # 使用convert_to_float函数将rank_name转换为浮点数
    value1 = convert_to_float(d1['rank_name'])
    value2 = convert_to_float(d2['rank_name'])
    
    # 比较两个浮点数
    if value1 < value2:
        return -1
    elif value1 > value2:
        return 1
    else:
        return 0


def save_log(log_str, log_path):
    with open(log_path, 'a') as f:
        f.write(log_str)
        f.close()



def get_chain_metadata(prompt_fn: Path, retrieve_module: bool = False) -> dict:
    """
    Get the metadata of the chain
    :param prompt_fn: The path to the prompt file
    :param retrieve_module: If True, retrieve the module
    :return: A dict with the metadata
    """
    prompt_directory = str(prompt_fn.parent)
    prompt_name = str(prompt_fn.stem)
    # print(prompt_directory)
    # print(prompt_name) 
    try:
        spec = importlib.util.spec_from_file_location('output_schemes', prompt_directory + '/output_schemes.py')
        schema_parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_parser)
    except ImportError as e:
        print(f"Error loading module {prompt_directory + '/output_schemes'}: {e}")
    if hasattr(schema_parser, '{}_parser'.format(prompt_name)):
        parser_func = getattr(schema_parser, '{}_parser'.format(prompt_name))
    else:
        parser_func = None
    result = {'parser_func': parser_func}
    if retrieve_module:
        result['module'] = schema_parser
        
    return result



def load_prompt(prompt_path: str, is_template: bool = True ) -> PromptTemplate:
    """
    Reads and returns the contents of a prompt file.
    :param prompt_path: The path to the prompt file
    """
    with open(prompt_path, 'r',encoding="utf-8") as file:
        prompt = file.read().rstrip()
    if is_template:
        return PromptTemplate.from_template(prompt)
    else:
        return prompt


def extract_csv_paths(text):
    csv_pattern = r'\./[a-zA-Z0-9_/]+\.csv'
    # 使用findall方法查找所有匹配的CSV文件路径
    csv_paths = re.findall(csv_pattern, text)
    return csv_paths


def parse_summary(correct_info ,summary):
    correct_info = str(correct_info)
    summary_str = ""
    final_answer_str = ""
    if correct_info != "":
        summary_str = "更正信息: " + correct_info + "\n"
    for file_path, answer_question,task_output_col in zip(summary['file_paths'], summary['questions'], summary['related_cols']):
        if file_path.startswith("/cache"):
            file_path = file_path.replace("/cache", "./cache")

        try:
            #注意三: 当读取文件不存在时，跳过
            if not os.path.exists(file_path):
                continue
            df = pd.read_csv(file_path)
            #注意三: 当数据为空，不打印数据
            if df.shape[0] == 0 :
                continue
            #注意三: 当为中间过程时,且数据数目大于10条时，不打印数据
            if file_path != summary['file_paths'][-1] and df.shape[0] > 20:
                continue
            
            #字段取交集
            set1 = set(df.columns)
            if "," in task_output_col:
                task_output_col = task_output_col.split(",")
            else:
                task_output_col = [task_output_col]
            set2 = set(task_output_col)
            intersection_col = list(set1 & set2)
            ###打印问题和数据
            df = df[intersection_col]
            summary_str += answer_question + '\n'
            
            if file_path == summary['file_paths'][-1] and df.shape[0] > 15 :
                summary_str += "最后的数据输出超过10条数据，已保存至本地文件 \n"
                for row in df.itertuples(index=False, name=None):
                    ###变为字符串进行打印
                    final_answer_str += ' '.join(map(str, row))
            else:
                for row in df.itertuples(index=False, name=None):
                    ###变为字符串进行打印
                    summary_str += ' '.join(map(str, row))

        except Exception as e:
            continue
        
    return final_answer_str, summary_str


def parse_task_list_csv_to_str(task_list):
    task_list_str = ""
    for key , value in task_list.items():
        csv_path = extract_csv_paths(value)
        for csv in csv_path:
            ##对数据量大于1前小于30的数据量进行记录,打印其全部数据量
            df = pd.read_csv(csv)
            if  len(df) < 30:
                need_cols = df.columns.tolist()
                task_list_str += f"任务编号{key},文件名{csv} 数据列名：{need_cols}，数据量：{len(df)}，数据量大于0前小于30的数据量，全部数据量：\n{df[need_cols].to_string(index=False)}\n"
            elif len(df) > 30:
                need_cols = list(set(df.columns.tolist()) & set(LISTED_ENTITY_COL_INFO))
                task_list_str += f"任务编号{key},文件名{csv} 数据列名：{df.columns.tolist()}，数据量：{len(df)}，数据量大于30的数据量, 全部数据量：\n{df[need_cols].to_string(index=False)}\n"
    return task_list_str


def parse_summary_csv_to_str(summary_str):
    task_list_str= summary_str
    csv_paths = extract_csv_paths(summary_str)
    for csv_path in csv_paths:
        df = pd.read_csv(csv_path)
        task_list_str = task_list_str.replace(csv_path, f"{csv_path} 数据如下：\n{df.to_string(index=False)}\n")

    return task_list_str


def parse_summary_csv_to_empty(summary_str):
    task_list_str= summary_str
    csv_paths = extract_csv_paths(summary_str)
    for csv_path in csv_paths:
        task_list_str = task_list_str.replace(csv_path, "")

    return task_list_str


def remove_comma_between_numbers(s):
    # 使用正则表达式找到两个数字之间的逗号，并将其去掉
    return re.sub(r'(?<=\d),(?=\d)', '', s)


def postprocess_summary(question, summary):
    try:
        summary = remove_comma_between_numbers(summary)
    except:
        summary = summary
    
    summary = parse_summary_csv_to_empty(summary)
    while "  " in summary:
        summary = summary.replace("  ", " ")
    
    summary = summary.replace("（", "(")
    summary = summary.replace("）", ")")

    summary = summary.replace("摄氏度", "度")
    summary = summary.replace("℃", "度")

    if "网址" in question:
        summary = summary + '-'

    return summary 