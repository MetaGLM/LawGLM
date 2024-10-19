import json
import re
from knowledge.api_info import TABLES
from Agent.Planer import Planer
from Agent.Executor import Executor
from Agent.llm import llm
from run_write import qisuzhuang_flow, zhenghebaogao_flow
from utils.post_processing import format_answer
from knowledge.prompt import answer_prompt
from utils.tips import get_tips
from threading import Lock
from run_query import format_history, preprocess_question, get_new_question
from utils.format_question import format_question

# 初始化全局锁
file_lock = Lock()


def add_message_log(messages, success=1):
    with open("log/message.jsonl", "a", encoding="utf8") as f:
        if success:
            f.write("执行成功:" + json.dumps(messages, ensure_ascii=False))
        else:
            f.write("执行失败:" + json.dumps(messages, ensure_ascii=False))
        f.write("\n")


def get_question(question, ner):
    res = preprocess_question(question, ner)
    if res["type"] == "任务完成":
        return question, format_history(res["history"]), True
    if len(ner["实体"]) == len(res["history"]):
        return question, "", False
    prompt = """
你会基于我给你的运行结果去提出新的问题。

以下是几个回答示例，解答完整参考此示例：

公司推理示例，你可以省略统一社会信用代码和公司代码。

示例：
问题为：91411625MA40GA2H02这家公司的母公司一共有多少家子公司，解答步骤为：{'名称': '91411625MA40GA2H02', '格式匹配为': '统一社会信用代码'}
使用 {'query_conds': {'统一社会信用代码': '91411625MA40GA2H02'}, 'need_fields': []} 查询结果:{'公司名称': '金丹生物新材料有限公司'}
使用 {'query_conds': {'公司名称': '金丹生物新材料有限公司'}, 'need_fields': ['关联上市公司全称', '公司名称']} 查询母公司结果:{'关联上市公司全称': '河南金丹乳酸科技股份有限公司', '公司名称': '金丹生物新材料有限公司'}，请直接输出新的问题：
你的回答：
已知答案：`金丹生物新材料有限公司`的统一社会信用代码为`91411625MA40GA2H02`，其母公司为`河南金丹乳酸科技股份有限公司`。
问题：`河南金丹乳酸科技股份有限公司`一共有多少家子公司？

问题为：原告是300077案件审理法院是什么时候成立的，解答步骤为：{'名称': '300077', '格式匹配为': '公司代码'}
使用 {'query_conds': {'公司代码': '300077'}, 'need_fields': ['公司名称', '公司代码']} 查询结果:{'公司名称': '国民技术股份有限公司', '公司代码': '300077'}
使用 {'query_conds': {'公司名称': '国民技术股份有限公司'}, 'need_fields': ['公司名称', '成立日期', '公司名称']} 查询结果: {'公司名称': '国民技术股份有限公司', '成立日期': '2000-03-20'}。
你的回答：
已知答案：公司代码为`300077`的公司是`国民技术股份有限公司`，其成立日期为`2000-03-20`。但是，这里存在一个问题，即原问题询问的是案件审理法院的成立时间，而不是公司的成立时间。
问题：原告是`国民技术股份有限公司`的案件审理法院是什么时候成立的？ 

地点推理示例，地址不可省略，不可对地址进行推理。
示例：
题目：问题为：(2020)冀民终207号案件中，审理当天原告的律师事务所与被告的律师事务所所在地区的最高温度相差多少度？，解答步骤为：{'名称': '(2020)冀民终207号', '格式匹配为': '案号'}
使用 {'query_conds': {'案号': '(2020)冀民终207号'}, 'need_fields': ['原告律师事务所', '被告律师事务所', '日期', '案号']} 查询结果: {'原告律师事务所': '北京市广盛律师事务所', '被告律师事务所': '河北至尊律师事务所', '日期': '2020-07-14 00:00:00', '案号': '(2020)冀民终207号'}
使用 {'query_conds': {'律师事务所名称': '北京市广盛律师事务所'}, 'need_fields': ['律师事务所地址', '律师事务所名称']} 查询结果: {'律师事务所地址': '北京市朝阳区东三环北路甲2号京信大厦15层', '律师事务所名称': '北京市广盛律师事务所'}
使用 {'query_conds': {'律师事务所名称': '河北至尊律师事务所'}, 'need_fields': ['律师事务所地址', '律师事务所名称']} 查询结果: {'律师事务所地址': '长江西街', '律师事务所名称': '河北至尊律师事务所'}。
你的答案：
已知答案：案件审理日期为`2020-07-14`，原告律师事务所位于`北京市朝阳区东三环北路甲2号京信大厦15层`，被告律师事务所位`长江西街`。
问题：`2020-07-14`，`北京市朝阳区东三环北路甲2号京信大厦15层`与`长江西街`所在地区的最高温度相差多少度？

问题为：(2019)川01民初1949号关联公司的注册地址在哪，该案的法院地址又在哪里，包括原告律师事务所所在的地址在内，这三个地址分别分布在几个省级行政区？，解答步骤为：{'名称': '(2019)川01民初1949号', '格式匹配为': '案号'}

使用 {'query_conds': {'案号': '(2019)川01民初1949号'}, 'need_fields': ['关联公司', '原告律师事务所', '案号']} 查询结果: {'关联公司': '中饮巴比食品股份有限公司', '原告律师事务所': '上海申浩（成都）律师事务所', '案号': '(2019)川01民初1949号', '审理法院': '四川省成都市中级人民法院'}
使用 {'query_conds': {'公司名称': '中饮巴比食品股份有限公司'}, 'need_fields': []} 查询结果: {'公司名称': '中饮巴比食品股份有限公司', '登记状态': '存续', '统一社会信用代码': '91310000558762442G', '法定代表人': '刘会平', '注册资本': '25011.375', '成立日期': '2010-07-08', '企业地址': '上海市松江区车墩镇茸江路785号', '联系电话': '4008979777', '联系邮箱': 'jituanban@zy1111.com', '注册号': '310112000994159', '组织机构代码': '55876244-2', '参保人数': '1127', '行业一级': '批发和零售业', '行业二级': '批发业', '行业三级': '食品、饮料及烟草制品批发', '曾用名': '中饮食品科技股份有限公司,\n上海中饮食品集团有限公司,\n上海中饮投资管理有限公司', '企业简介': '中饮巴比食品股份有限公司注册地位于上海市松江区，注册资本1.68亿人民币，以早餐食品生产、连锁经营为主业，兼营物流管理、电子商务、地产开发、文化创意等。集团核心成员企业横跨沪、皖两地，均为在当地享有较高知名度和影响力的民营企业。自集团创始人刘会平2003年在上海创立“巴比”馒头品牌以来，我们秉承“品牌化、专业化、规模化、标准化”的经营理念，坚持以“工业化生产、生冷链配送、门店连锁化销售、团体供餐为一体”的商业模式，以“品牌、服务、质量”为先导，以科技创新为动力，全心为广大市民提供美味、新鲜、健康、安全的早餐食品。经过多年对早餐市场的专注经营，集团已成为中国早餐市场着名企业，特别是在长三角地区，已成为公认的早餐市场第一品牌企业。目前拥有上海目前规模最大的大众化早点食品加工中心，在职员工1000余人。公司管理成熟，形象良好，多年来被中央电视台、上海卫视、安徽卫视、人民日报、解放日报、文汇报、环球时报等众多媒体广泛报道，载誉无数，连续多年荣获“中国餐饮百强”、“松江区先进企业”称号，2011年商务部“早餐示范工程”承建单位，2012年、2013年 上海市“早餐工程先进单位”， 2014年荣获“上海市名牌企业”称号。核心品牌“巴比”馒头，在社会上具有很高的知名度和市场占有率，2013年“巴比”获“上海市着名商标”称号。截至目前，“巴比”馒头在长三角拥有2000多家专卖店，200个固定团体供餐点，保证每日数百万人早餐供应。集团成员企业还包括专业冷链物流企业上海中饮物流有限公司、地产投资管理企业安徽中饮投资有限公司等。电子商务、文化创意、动漫制作等新兴产业是中饮集团正在筹划的产业发展方向。其中，电子商务O2O平台的打造已形成初步规划，动漫系列形象和系列动画片的创意已完成框架搭建。中饮集团的中长期发展目标是：努力打造拥有中国第一品牌的国民级健康早餐连锁企业和国内知名的中式面点制造企业；巴比馒头品牌努力在2016年前实现中国驰名商标；建立中国早餐行业最完善的经营管理体系；建立完善的员工激励机制，不断提升员工福利，构建一支真诚、团结、务实、创新的管理团队；建成从初级农产品（含畜产品）一级采购市场到食品与餐饮行业消费终端的农产品产业链，建成从创意设计到文化消费品制作与发行的文化创意产业链。', '经营范围': '食品流通 ，食品生产，食品科技领域内的技术开发、技术转让、技术咨询、技术服务，餐饮企业管理，食用农产品、厨房设备、电器设备、电子产品、百货、服装鞋帽、广告灯箱、包装材料的销售，粮食收购，投资管理，实业投资，投资咨询，企业管理咨询，自有房屋租赁，自有设备租赁，道路货物运输，广告设计、制作，展览展示服务，从事货物及技术的进出口业务。【依法须经批准的项目，经相关部门批准后方可开展经营活动】'}
使用 {'query_conds': {'律师事务所名称': '上海申浩（成都）律师事务所'}, 'need_fields': ['律师事务所地址', '律师事务所名称']} 查询结果: {'律师事务所地址': '锦江区红星路三段1号43层4302-06单元', '律师事务所名称': '上海申浩（成都）律师事务所'}
使用 {'query_conds': {'法院名称': '四川省成都市中级人民法院'}, 'need_fields': ['法院地址', '法院名称']} 查询结果: {'法院地址': '四川省成都市金牛区抚琴西路109号', '法院名称': '四川省成都市中级人民法院'}。
你的回答：
已知答案：关联公司`中饮巴比食品股份有限公司`的注册地址为`上海市松江区车墩镇茸江路785号`，原告律师事务所`上海申浩（成都）律师事务所`的地址为`锦江区红星路三段1号43层4302-06单元`，案件`(2019)川01民初1949号`的法院`四川省成都市中级人民法院`的地址为`四川省成都市金牛区抚琴西路109号`。
问题：`上海市松江区车墩镇茸江路785号`，`锦江区红星路三段1号43层4302-06单元`，`四川省成都市金牛区抚琴西路109号`，这三个地址分别分布在几个省级行政区

问题为：集安市人民法院所在的区县区划代码是多少，解答步骤为：{'名称': '集安市人民法院', '格式匹配为': '法院名称'}
使用 {'query_conds': {'法院名称': '集安市人民法院'}, 'need_fields': ['法院代字', '法院名称']} 查询结果:{'法院代字': '吉0582', '法院名称': '集安市人民法院'}
使用 {'query_conds': {'法院名称': '集安市人民法院'}, 'need_fields': ['法院代字', '法院名称']} 查询结果: {'法院代字': '吉0582', '法院名称': '集安市人民法院'}。
你的回答：
已知答案：集安市人民法院的法院代字为`吉0582`。
问题：`集安市人民法院`所在的区县区划代码是多少？

示例：
问题为：(2023)津0116执29434号的限高执行法院为哪个法院?被限高公司的法定代表人是谁?限高的申请人是谁?总涉案金额是多少。这个执行法院的法院级别是什么?他的法院负责人是谁。，解答步骤为：{'名称': '(2023)津0116执29434号', '格式匹配为': '案号'}
使用 {'query_conds': {'案号': '（2023）津0116执29434号'}, 'need_fields': ['执行法院', '法定代表人', '申请人', '涉案金额', '案号']} 查询结果: {'执行法院': '天津市滨海新区人民法院', '法定代表人': '黄春奇', '申请人': '天津市凯成房地产咨询有限公司', '涉案金额': '2054659.34', '案号': '（2023）津0116执29434号'}
使用 {'query_conds': {'法院名称': '天津市滨海新区人民法院'}, 'need_fields': ['法院负责人', '法院名称']} 查询结果: {'法院负责人': '张长山', '法院名称': '天津市滨海新区人民法院'}，请直接输出新的问题。
你的回答：已知答案：执行法院为`天津市滨海新区人民法院`，法定代表人为`黄春奇`，申请人为`天津市凯成房地产咨询有限公司`，涉案金额为`2054659.34元`，法院负责人为`张长山`。
问题：`天津市滨海新区人民法院法院`级别是什么？

请注意你的提问一定要完整,如果有新的已知条件，要在题目后面备注，但是不要自己猜测，例如知道法院代字，则在法院后面加上（法院代字为：xxx）.
对于统一社会信用代码和公司简称以及母公司，你可以推测主语，从而省略部分主语，不要做任何地点的推断，问题中必须包含完整的实体不要有任何指代。
你一定要使用我给你的已知条件里的字段，不要添加任何推理（替换公司简称和统一社会信用代码以及母公司除外），字段使用 `` 注明,如果没有任何有用信息，请一字不差的返回原问题。
"""
    answer = format_history(res["history"])
    question_flow = [{"role": "system", "content": prompt}]
    question_flow.append(
        {
            "role": "user",
            "content": f"""问题为：{question}，解答步骤为：{answer}。
你的回答：""",
        }
    )
    resp = llm(question_flow)
    return resp.split("问题", 1)[-1].lstrip("：").split("\n")[0], answer, False


def coder(question, check_api):
    log_all = ""
    planer = Planer(question)
    executor = Executor(question, planer.flow, max_try_num=3)
    step_prompt = planer.get_next_step()
    while True:
        res = executor.handle_one_step(step_prompt)
        if "error_log" in res:
            return log_all + executor.qa_content, False, False
        else:
            step_prompt = planer.get_next_step()
        if step_prompt is None:
            break
    add_message_log({"question": question, "message": executor.messages})

    executor.code_kernel.shutdown()
    if executor.err_num > 3:
        plan = None
    else:
        plan = planer.plan_answer
    if check_api:
        final_answer = log_all + executor.qa_content + planer.get_api_num()
    else:
        final_answer = log_all + executor.qa_content
    return final_answer, True, plan


def question_coder(question, check_api=False, do_process=True, is_retry=False):
    if check_api:
        do_process = False
    if do_process:
        question = format_question(question)
        raw_question = question
        tips, ner = get_tips(question)
        try:
            question, answer0, answered = get_question(question, ner)
        except Exception:
            import traceback

            traceback.print_exc()
            answer0 = ""
            answered = False

    else:
        raw_question = question
        tips, ner = get_tips(question)
        answer0 = ""
        answered = False

    if check_api:
        prompt = (
            answer_prompt
            + "\n我会给你API的计划调用情况，一般是正确答案，特殊情况会说明，你只需要回答题目里问到的API使用情况，不要多回答"
        )
    else:
        prompt = answer_prompt
    question_flow = [{"role": "system", "content": prompt}]
    answer = ""
    if not answered:
        if do_process:
            tips, ner = get_tips(question)

        question_tips = f"你需要专注的问题为:`{question}`\n{tips}"

        answer, flag, plan = coder(question_tips, check_api)
        answer = answer.split("解答步骤")[-1]
        answer = [i.strip("`") for i in answer.split("\n")[2:] if not re.match("```|答案|任务已完成|--|ipython", i)]

    # 正则表达式来匹配并捕获值
    pattern = re.compile(r"\{'query_conds': \{(.+?)\}")
    answer = answer0 + "\n" + "\n".join(answer)
    matches = pattern.findall(str(answer), re.DOTALL)
    key = re.findall("'(.*?)'", " ".join(matches))
    msg = ""
    if "'-'" in answer:
        msg = "记住 '-'也是答案。"
    if check_api:
        msg += "记住api调用不要多答。"
    if "小数" in raw_question:
        msg += "注意小数位数。"
    if re.search("多少家|几家|多少个|几个|多少起|几起|几件|多少件", raw_question):
        msg += "不仅需要回答数量，还要需要列举符合条件的公司/案号。"
    question_flow.append(
        {
            "role": "user",
            "content": f"""
问题为：{raw_question}
解答步骤为：
--
{answer}
--
关键节点为：{key}。
请整理成问题的答案,关键节点一定要在答案中，有冲突的名称以关键节点为准。
其中过程案号,地点,公司名等信息不可省略，要从过程中找到正确的。
即使问题没有被完全回答，也要从第一步进行推理，无法得知的部分用[未知]代替，用户可能会输入错误以关键节点为准。
从步骤的第一步开始整理，使用自然语言，不要出现代码格式，也不要计算，回答再包含所有关键节点的时候尽可能简洁，单位与题目保持一致。
参照示例格式给出答案。
{msg}
你的答案：""",
        }
    )
    answer1 = llm(question_flow)
    answer = answer1.split("关键节点")[0]
    if do_process and not is_retry:
        if "未知" in answer1 or "无法" in answer1:
            if answered:  # 如果是仅查询答题完成
                answer, key = question_coder(raw_question, do_process=False, is_retry=True)
            else:
                new_question = get_new_question(raw_question, answer)
                if "解答失败" not in new_question:
                    new_answer, key2 = question_coder(new_question, is_retry=True)
                    msg = ""
                    if "'-'" in new_answer:
                        msg = "记住 '-'也是答案"
                    question_flow.append(
                        {
                            "role": "user",
                            "content": f"""问题为：{raw_question}
之前的答案为：{answer}
现在有了更新：{new_answer},
请更新答案，将之前答案未知的部分替换成答案，其他地方不要改变，不要分析，不要解释，只做替换。
简单分析后给出答案。{msg}
更新后的答案：""",
                        }
                    )

                    answer = llm(question_flow)
                    key.extend(key2)
    return answer.replace("[未知]", "-"), key


def process_question(data, result_path="/app/result.json"):
    data["answer"] = ""
    key = []
    try:
        answer = None
        if re.search("整合|word", data["question"].replace(" ", ""), re.IGNORECASE):
            answer = zhenghebaogao_flow(data["question"])
        if re.search("写一份|起诉状", data["question"]):
            answer = qisuzhuang_flow(data["question"])

        if answer is None:
            if re.search("ＡＰＩ|API|api|接口", data["question"].replace(" ", "")):
                answer, key = question_coder(data["question"], check_api=True)
            else:
                answer, key = question_coder(data["question"])

        answer = format_answer(data["question"], answer)
        for i in set(key):
            if i not in str(TABLES):
                i = i.replace("（", "(").replace("）", ")")
                if i not in answer and re.search("[\u4e00-\u9fa5]", i) and not re.search("年.*月.*日", i):
                    answer += i

        with file_lock:
            with open(result_path, "r", encoding="utf8") as f:
                all_answer = f.read()
            with open(result_path, "w", encoding="utf8") as f:
                s1 = json.dumps(data, ensure_ascii=False)
                data["answer"] = answer
                s2 = json.dumps(data, ensure_ascii=False)
                new_answer = all_answer.replace(s1, s2)
                print("\n\n")
                print(new_answer.replace("\n", "###"))
                f.write(new_answer)
        return data
    except:
        import traceback

        traceback.print_exc()
        return data


from concurrent.futures import ThreadPoolExecutor


def main():
    with open("data/question_c2.json", encoding="utf8") as f:
        questions = [json.loads(line) for line in f]

    with open("result.json", "a", encoding="utf8") as f:
        for i in questions:
            i["answer"] = ""
            f.write(json.dumps(i, ensure_ascii=False))
            f.write("\n")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_question, questions)


if __name__ == "__main__":
    question_coder(
        "航天机电公司投资最高的公司，涉诉案件在哪几家法院进行审理？涉案金额最高的案由为？其中审理案件最基层的法院成立日期提供一下",
        check_api=True,
    )
