import jsonlines
from tqdm import tqdm
from utils import read_jsonl
from config import *

if __name__ == "__main__":
    question_file = "./data/questions/B_question.json"
    result_file = "data/0/nickolasNi_result.json"
    queries = read_jsonl(question_file)
    print_log("Start generating answers...")

    for query in tqdm(queries):
        result = ""
        content = {"id": query["id"], "question": query["question"], "answer": result}
        with jsonlines.open(result_file, "a") as json_file:
            json_file.write(content)