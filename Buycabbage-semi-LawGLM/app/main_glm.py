import audit_agent
import suzhuang_agent
import sbaogao_agent
import run_v2
import tools
import API_diaoyong
import run_v6
import re


def get_answer_2(question):
    try:
        print(f"尝试使用方法2回答问题: {question}")
        tools_all = tools.tools_all
        answer, function_result_logger = run_v2.get_answer_2(question, tools_all)
        answer = run_v2.answer_yh(question, answer, function_result_logger)
        answer_a = API_diaoyong.API_diaoyong_agent(question, answer)
        return answer_a
    except Exception as e:
        print(f"方法2执行时发生错误: {e}")
        return "方法2无法回答，出现了错误。"
def get_answer_8(question):
    try:
        print(f"尝试使用方法8回答问题: {question}")
        last_answer = run_v6.run_conversation_psby(question)
        return last_answer
    except Exception as e:
        print(f"方法8执行时发生错误: {e}")
        return "方法8无法回答，出现了错误。"


def replace_date_format(text):
    try:
        pattern = r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})日?"
        result = re.sub(pattern, lambda m: f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日", text)
        replacements = {"（": "(", "）": ")", "【": "(", "】": ")", "℃": "度", "'": ""}
        trans = str.maketrans(replacements)
        result = result.translate(trans)
        matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", result)
        for match in matches:
            result = result.replace(match, match.replace(",", ""))
        return result
    except Exception as e:
        print(f"在尝试回答问题时出现未知错误: {e}")
        return text


def main_answer(question):
    answer_method2_correct = False
    answer_method3_correct = False
    try:
        if "诉状" in question:
            answer, function_result_logger = suzhuang_agent.get_answer_sz(question)
            answer = str(function_result_logger)
        elif "整合报告" in question:
            answer = sbaogao_agent.bg_yz(question)

        else:
            answer = get_answer_8(question)
            answer_9 = answer
            if "无法" in answer or "没有" in answer:  # 取消大模型判断
                answer = get_answer_8(question)
                answer_8 = answer
                if "无法" in answer or "没有" in answer:
                    print("-------选择模型-------")
                    answer_2 = get_answer_2(question)
                    answer = audit_agent.audit_agent_model_ensembling_1(question, answer_9, answer_8, answer_2)
    except Exception as e:
        print(f"在尝试回答问题时出现未知错误: {e}")
        answer = "由于错误，无法提供答案。"

    print("模型的最终答案是：", answer)
    final_answer_status = (
        "方法2正确回答"
        if answer_method2_correct
        else ("方法3正确回答" if answer_method3_correct else "都没有正确回答")
    )
    answer = replace_date_format(answer)
    return answer, final_answer_status


if __name__ == "__main__":

    main_answer('保定市天威西路2222号地址对应的省市区县分别是？')
