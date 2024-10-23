from zhipuai import ZhipuAI
import requests
import json
import re
import os
from D_tools import TOOLS

from new_logtool import VLOG

MAX_RETRY = 3
API_KEY = ""
CLIENT = ZhipuAI(api_key=os.getenv("OPENAI_API_KEY"))


class LLM:
    @staticmethod
    def get_llm(query, temperature=0.1, model="glm-4", do_sample=False):  # glm-4-air
        response = CLIENT.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": query},
            ],
            stream=False,
            do_sample=do_sample,
            temperature=temperature,
        )
        return response.choices[0].message.content

    @staticmethod
    def get_json_response(query, max_retries=MAX_RETRY):
        response = TOOLS.prase_json_from_response(LLM.get_llm(query))
        VLOG[2](response)
        if not response:
            try:
                response = json.loads(response)
                return response
            except Exception as e:
                VLOG[2](f"解析失败，错误信息：{e}")
        return response

    @staticmethod
    def get_case_id(case_id):
        pattern = re.compile(r"([\u4e00-\u9fa5])\1+")
        new_case_id = pattern.sub(r"\1", case_id)
        new_case_id = new_case_id.replace("【", "(").replace("】", ")").replace("（", "(").replace("）", ")")
        year = re.search(r"\d{4, 10}", new_case_id)
        if year and len(year.group()) > 4:
            pattern = re.compile(r"(.)\1")
            new_year = pattern.sub(r"\1", year.group())
            new_case_id = new_case_id.replace(year.group(), new_year)

        if new_case_id[0] != "(":
            new_case_id = "(" + new_case_id
            if ")" not in new_case_id:
                new_case_id = new_case_id[0:5] + ")" + new_case_id[5:]

        try:
            new_case_id = TOOLS.caseid_search2(new_case_id)[0]
        except Exception as e:
            VLOG[2](f"ERROR: {e}")

        VLOG[2]("NEW_CASE_ID:", new_case_id, "|", case_id)
        return new_case_id

    @staticmethod
    def get_case_id2(case_id):
        new_case_id = case_id.replace("(", "（").replace(")", "）")
        return new_case_id

    @staticmethod
    def answer_simple(question, info, history_info=[], important_info=[]):
        if len(important_info) > 0:
            prompt = f"""
【问题】{question}


【查询信息】{info}


【此步骤重要信息】{important_info}


【历史上下文信息】{history_info}


请根据信息，整合答案，直接给出简洁、完整且清晰的回答。主体信息必须要保留，此步骤重要信息必须保留，不要回答和问题无关的内容。
回答：
""".strip()
        else:
            prompt = f"""
【问题】{question}


【查询信息】{info}


【历史上下文信息】{history_info}


请根据信息，整合答案，直接给出简洁、完整且清晰的回答。主体信息必须要保留，不要回答和问题无关的内容。
回答：
""".strip()
        final_answer = LLM.get_llm(query=prompt, model="glm-4", do_sample=False)
        return final_answer

    @staticmethod
    def refine_answer_info(question, info=[], history_info=[]):
        if len(str(info)) > 5000:
            info = info[0:5000]

        prompt = f"""
【问题】{question}


【当前信息】{info}


【历史信息】{history_info}


请根据当前信息和历史信息，整合答案，直接给出简洁、完整且清晰的回答。回答格式忠于提问方式。不要回答问题之外的内容。
回答：
""".strip()

        final_answer = LLM.get_llm(query=prompt, do_sample=False)
        return final_answer

    @staticmethod
    def refine_answer_history(question, history_info=[]):
        history_info_str = "\n\n".join([str(x) for x in history_info])
        prompt = f"""
现在要解决以下大问题：
问题：{question}


在解决这个问题的过程中，已经解决了以下中间步骤问题和答案：
{history_info_str}


请根据信息，整合答案，给出完整且清晰的回答，原问题里的所有内容都要回答，且主体信息（例如公司名称、案号等）必须保留。中间步骤获取的信息（尤其是该步骤重要信息）需要整合到回答中。
和问题没有关联的内容可以省略。无需解释解题思路，无需解释未知内容，无需建议。
回答：
        """.strip()
        final_answer = LLM.get_llm(query=prompt, do_sample=False)
        return final_answer

    @staticmethod
    def refine_answer_data(question, history_info=[], data=[]):
        if len(str(data)) > 5000:
            data = str(data)[0:5000]
        history_info_str = "\n\n".join([str(x) for x in history_info])
        prompt = f"""
问题：{question}


中间步骤问题和答案：{history_info_str}


中间步骤获取的部分信息：{data}


请根据信息，整合答案，给出完整且清晰的回答，原问题里的所有内容都要回答，且主体信息（例如公司名称、案号等）必须保留。中间步骤获取的信息（尤其是该步骤重要信息）需要整合到回答中。
和问题没有关联的内容可以省略。无需解释解题思路，无需解释未知内容，无需建议。
回答：
        """
        final_answer = LLM.get_llm(query=prompt, do_sample=False)
        return final_answer

    @staticmethod
    def refine_answer_simple(question, answer, important):
        prompt = f"""
问题：{question}

初步答案：{answer}

在获得初步答案过程中的关键实体名称：{important}

针对问题，已知有如上初步答案，请根据问题描述，润色答案，将关键实体名称融合到答案中，回答务必保持答案简洁，不要回答和问题无关的内容，字数越少越好。需要保留和问题有关联的主体信息（请务必保留各个主体信息具体的名称，例如公司名称、案号等）。
和问题没有关联的内容可以省略，未知内容可以省略。特别注意，原问题中的所有内容都要回答，且相关的主体信息必须保留。
无需解释解题思路，无需解释未知内容，无需建议，无需补充，无需说明根据查询信息或已经提供的信息，直接回答即可。无法获得的信息不用回答，不要额外补充各种建议和说明。
        """.strip()
        final_answer = LLM.get_llm(query=prompt, do_sample=False)
        return final_answer

    @staticmethod
    def refine_answer_final(question, answer):
        new_answer = answer
        if "摄氏度" in new_answer or "℃" in new_answer:
            new_answer = new_answer.replace("摄氏度", "度").replace("℃", "度")
            VLOG[2]("###", new_answer)
        new_answer = new_answer.replace("（", "(").replace("）", ")").replace("【", "(").replace("】", ")")
        new_answer = (
            new_answer.replace("根据查询结果，", "")
            .replace("根据查询结果", "")
            .replace("根据查询", "")
            .replace("根据提供信息，", "")
        )
        # new_answer = new_answer.replace("问题：", "").replace(question, "").replace("回答：", "")
        new_answer = new_answer.strip()
        try:
            # caseid_list = TOOLS.caseid_search2(question)
            # for caseid in caseid_list:
            #     if caseid not in new_answer:
            #         new_answer = caseid + new_answer

            res = re.findall(r"年\d{1,2}月\d{1,2}日", new_answer)
            if res:
                for x in res:
                    month = x.split("年")[1].split("月")[0]
                    date = x.split("月")[1].split("日")[0]
                    if len(month) == 1:
                        month = "0" + month
                    if len(date) == 1:
                        date = "0" + date
                    new_x = "年" + month + "月" + date + "日"
                    new_answer = new_answer.replace(x, new_x)
                    VLOG[2]("###", new_answer)

            if "," in new_answer and re.search(r"\d+,\d+", new_answer):
                for i in range(new_answer.count(",")):
                    new_answer = re.sub(r"(\d+),(\d+)", r"\1\2", new_answer)
                    VLOG[2]("###", i, new_answer)

            if "保留2位" in question or "保留两位" in question:
                res = re.findall(r"-?\d+\.\d+", new_answer) + re.findall(r"[\u4e00-\u9fa5]{1}\d+元", new_answer)
                if res:
                    for x in res:
                        VLOG[2](x)
                        if x[-1] == "元":
                            x = x[1:-1]
                            new_x = round(float(x), 2)
                            new_str = x[0] + str("%.2f" % new_x) + "元"
                        else:
                            new_x = round(float(x), 2)
                            new_str = str("%.2f" % new_x)
                        new_answer = new_answer.replace(x, new_str)
                        VLOG[2]("---", question)
                        VLOG[2]("###", new_answer)

            if "保留1位" in question or "保留一位" in question:
                res = re.findall(r"-?\d+\.\d+", new_answer) + re.findall(r"[\u4e00-\u9fa5]{1}\d+元", new_answer)
                if res:
                    for x in res:
                        VLOG[2](x)
                        if x[-1] == "元":
                            x = x[1:-1]
                            new_x = round(float(x), 1)
                            new_str = x[0] + str("%.1f" % new_x) + "元"
                        else:
                            new_x = round(float(x), 1)
                            new_str = str("%.1f" % new_x)
                        new_answer = new_answer.replace(x, new_str)
                        VLOG[2]("---", question)
                        VLOG[2]("###", new_answer)

            # if "亿" not in question and "万" not in question:
            #     res = re.findall(r'-?\d+\.?\d*亿', new_answer)
            #     VLOG[2](res)
            #     if res:
            #         for x in res:
            #             new_x = float(x[0:-1]) * 10**8
            #             new_answer = new_answer.replace(x, str(new_x))

            #     res2 = re.findall(r'-?\d+\.?\d*万', new_answer)
            #     VLOG[2](res2)
            #     if res2:
            #         for x in res2:
            #             new_x = float(x[0:-1]) * 10**4
            #             new_answer = new_answer.replace(x, str(new_x))
        except Exception as e:
            VLOG[2](f"ERROR: {e}")
        return new_answer

    @staticmethod
    def refine_question(question):
        # pattern = r'(?<!\d)\d{6}(?!\d)'
        # matches = re.findall(pattern, question)
        # for match in matches:
        #     question = question.replace(match, match+"(公司代码)")

        # question = TOOLS.caseid_augment(question)

        pattern = r"([a-zA-Z0-9]{18,30})"
        res = re.search(pattern, question)
        pattern2 = r"(\d{6,17})"
        res2 = re.search(pattern2, question)

        res3 = "号" in question
        if res:
            question = question.replace(res.group(), res.group() + "(公司社会统一信用代码)")
        elif res2 and not res3:
            question = question.replace(res2.group(), res2.group() + "(公司代码)")

        pattern = r"(\d{1,6}号)"
        if re.search(pattern, question) and "地址" not in question:
            question = re.sub(pattern, r"\1(案号)", question)

        wrong_words_map = {"邮箱地址": "邮箱和地址", "圈资": "全资", "限告": "限高", "温洲": "温州"}
        for wrong_word, right_word in wrong_words_map.items():
            if wrong_word in question:
                question = question.replace(wrong_word, right_word)

        if "事务所" in question and "律师事务所" not in question:
            question = question.replace("事务所", "律师事务所")

        prompt = f"""
已知用户问题：{question}

请根据问题描述，写明用户想查询的信息，直接回复，不要回答问题，不要输出其它内容，回复越简洁越好。
""".strip()

        if len(question) > 40:
            res = LLM.get_llm(query=prompt, do_sample=False)

        VLOG[2]("NEW_QUESTION:", question, res)
        return question + "（用户核心诉求：" + res + "）"


if __name__ == "__main__":
    question = "总额多少？(保留2位小数)"
    new_answer = "一共23,100.2亿元。"

    VLOG[2](LLM.refine_answer_final(question, new_answer))
