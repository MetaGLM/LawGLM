import jsonlines
from tqdm import tqdm

import get_known


def read_jsonl(path):
    # 初始化空列表，用于存储读取到的内容
    content = []
    # 使用jsonlines库打开jsonl文件，并设置为只读模式
    with jsonlines.open(path, "r") as json_file:
        # 遍历json文件的每一行，将其转换为字典类型
        for obj in json_file.iter(type=dict, skip_invalid=True):
            # 将每一行添加到content列表中
            content.append(obj)
    # 返回content列表
    return content


question_file = "datas/b_question.json"
# 修改输出文件
result_file = "saltfire_result.json"
queries = read_jsonl(question_file)

# 生成答案
print("开始生成答案")

for query in tqdm(queries):
    answer_1, answer1 = get_known.getanswer(query["question"])
    answer0 = answer_1.content

    content = {"id": query["id"], "question": query["question"], "answer": answer0}
    print(f"写入回答：{content}")
    with jsonlines.open(result_file, "a") as json_file:
        json_file.write(content)


# print(get_known.getanswer('我想要联系上海妙可蓝多食品科技股份有限公司的法人代表，请问他的名字是什么？').content)
# print(1)
