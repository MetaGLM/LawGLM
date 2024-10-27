import jsonlines
from tqdm import tqdm
from utils import read_jsonl
from config import *

if __name__ == "__main__":
    question_file = "./data/questions/B_question.json"
    # 修改输出文件
    # result_file = "data/results/nickolasNi_result.json"
    result_file = "data/0/nickolasNi_result.json"
    queries = read_jsonl(question_file)

    # 生成答案
    print_log("Start generating answers...")

    for query in tqdm(queries):
        result = ""
        content = {"id": query["id"], "question": query["question"], "answer": result}
        with jsonlines.open(result_file, "a") as json_file:
            json_file.write(content)

        # message_file_path = 'data/message/' + str(query['id']) + '.json'
        # import json
        # with open(message_file_path, 'w', encoding='utf-8') as file:
        #     json.dump(response[2], file, ensure_ascii=False, indent=4)
        # print_log('{} tokens used'.format(str(response[0])))
        #
        # # save tools to json
