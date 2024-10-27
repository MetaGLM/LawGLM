# -*- coding: utf-8 -*-
"""
Created on Sat Jul 13 09:39:14 2024

@author: 86187
"""

import audit_agent
import suzhuang_agent
import sbaogao_agent
import run_v2
import task_decomposition_v1
import tools
import API_diaoyong
import run_v6
import re


def get_answer_2(question):
    try:
        print(f"尝试使用方法2回答问题: {question}")
        # 这里应添加逻辑来生成或获取答案，可能会抛出异常
        tools_all = tools.tools_all
        answer, function_result_logger = run_v2.get_answer_2(question, tools_all)
        answer = run_v2.answer_yh(question, answer, function_result_logger)
        answer_a = API_diaoyong.API_diaoyong_agent(question, answer)
        return answer_a
    except Exception as e:
        print(f"方法2执行时发生错误: {e}")
        return "方法2无法回答，出现了错误。"


def get_answer_3(question):
    try:
        print(f"尝试使用方法3回答问题: {question}")
        # 同上，但使用不同的方法或来源获取答案，也有可能抛出异常
        tools_all = tools.tools_all
        answer = task_decomposition_v1.sub_answer(question, tools_all)
        answer_a = API_diaoyong.API_diaoyong_agent(question, answer)
        return answer_a
    except Exception as e:
        print(f"方法3执行时发生错误: {e}")
        return "方法3无法回答，出现了错误。"


def get_answer_6(question):
    try:
        print(f"尝试使用方法6回答问题: {question}")
        # 同上，但使用不同的方法或来源获取答案，也有可能抛出异常
        answer_a, _ = run_v6.run_conversation_xietong(question)
        answer_a = str(answer_a)
        answer_a = (
            answer_a.replace("全部完成，答案如下：", "")
            .replace("全部完成，答案如下", "")
            .replace("`", "")
            .replace("<>：", "")
        )
        return answer_a
    except Exception as e:
        print(f"方法3执行时发生错误: {e}")
        return "方法3无法回答，出现了错误。"


def get_answer_7(question):
    try:
        print(f"尝试使用方法6回答问题: {question}")
        # 同上，但使用不同的方法或来源获取答案，也有可能抛出异常
        last_answer, messages_1 = run_v6.run_conversation_xietong(question)
        text = run_v6.run_conversation_tiqu(messages_1)
        return text
    except Exception as e:
        print(f"方法3执行时发生错误: {e}")
        return "方法3无法回答，出现了错误。"


def get_answer_8(question):
    try:
        print(f"尝试使用方法8回答问题: {question}")
        # 同上，但使用不同的方法或来源获取答案，也有可能抛出异常
        last_answer = run_v6.run_conversation_psby(question)
        # last_answer=audit_agent.audit_agent_model_ensembling(question,last_answer)  #若不使用该功能直接注释掉即可，不影响程序正常运行  但要开始audit自我判断功能
        return last_answer
    except Exception as e:
        print(f"方法8执行时发生错误: {e}")
        return "方法8无法回答，出现了错误。"


def replace_date_format(text):
    try:
        # 使用正则表达式查找形如"YYYY-MM-DD"和"YYYY年MM月DD日"的日期格式
        pattern = r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})日?"
        # 使用正则表达式替换找到的日期格式
        result = re.sub(pattern, lambda m: f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日", text)

        # 定义中文括号到英文括号的映射
        replacements = {"（": "(", "）": ")", "【": "(", "】": ")", "℃": "度", "'": ""}
        # 使用str.translate和str.maketrans创建翻译表
        trans = str.maketrans(replacements)
        # 替换文本中的中文括号为英文括号
        result = result.translate(trans)

        # 使用正则表达式找到数字和逗号的部分
        matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", result)
        for match in matches:
            # 移除逗号并替换原始字符串中的匹配部分
            result = result.replace(match, match.replace(",", ""))
        return result
    except Exception as e:
        # 如果有任何异常发生，返回原始文本
        print(f"在尝试回答问题时出现未知错误: {e}")
        return text


def main_answer(question):
    # question = "(2021)豫0302民初674号的起诉日期是哪个年份，审理日期为，审理法院是？审理法院的地址是？审理法院地址所在区县是？"
    # question='统一代码9165292274222840XN这家公司作为原告的案件中，它雇佣的律师事务所的联系方式是什么'
    answer_method2_correct = False
    answer_method3_correct = False
    try:
        # 首先尝试使用get_answer_2
        if "诉状" in question:
            answer, function_result_logger = suzhuang_agent.get_answer_sz(question)
            answer = str(function_result_logger)
        elif "整合报告" in question:
            answer = sbaogao_agent.bg_yz(question)
        # elif '913401007885810000' in question or '成地香港'  in question  or  '上海飞科电器股份有限公司'  in question :
        #    answer=question+'该问题无查询结果'  ############节约tokens
        else:
            answer = get_answer_8(question)
            # if not audit_agent.audit_agent(question, answer):  #取消大模型判断
            answer_9 = answer
            if "无法" in answer or "没有" in answer:  # 取消大模型判断
                answer = get_answer_8(question)
                answer_8 = answer
                if "无法" in answer or "没有" in answer:
                    print("-------选择模型-------")
                    answer_2 = get_answer_2(question)
                    # answer_3=get_answer_3(question)
                    answer = audit_agent.audit_agent_model_ensembling_1(question, answer_9, answer_8, answer_2)
    except Exception as e:
        print(f"在尝试回答问题时出现未知错误: {e}")
        answer = "由于错误，无法提供答案。"

    # 不论是哪种方法回答的，最后都再次检查
    # if audit_agent.audit_agent(question, answer):
    #     print(f"问题'{question}'已正确回答：{answer}")
    #    answer_method3_correct = True
    # else:
    #      print(f"问题'{question}'未能得到正确回答。")
    print("模型的最终答案是：", answer)
    final_answer_status = (
        "方法2正确回答"
        if answer_method2_correct
        else ("方法3正确回答" if answer_method3_correct else "都没有正确回答")
    )
    answer = replace_date_format(answer)
    return answer, final_answer_status


if __name__ == "__main__":
    # question='我是一家律师事务所的律师，我的委托人的子公司准备起诉一家上市公司，想要准备起诉书，我们已经查询过该公司工商信息中的法人及电话，电话打不通人名也对不上，请帮我查询一下该上市公司的法人信息及电话吧，该上市公司的全称为浙江海正药业股份有限公司。'
    # question='廊坊市凯宏家居广场有限公司的统一信用代码是？投资该公司的母公司是？被投资的比例与金额分别是？该公司2019年是否被起诉次数及涉案总额为？'
    # question='山东潍坊润丰化工股份有限公司投资金额最高的子公司与投资最低的子公司注册地址所在城市分别是？串行了几类API？串行了几次？'
    # answer,final_answer_status=main_answer(question)

    # print('-------------最终答案如下-----------------')
    # print(answer)
    print(str(replace_date_format("'")))
