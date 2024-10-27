import json
import concurrent.futures as cf
import main_glm


def process_one(question_json):
    line = question_json
    query = line["question"]

    answer, final_answer_status = main_glm.main_answer(query)
    ans = str(answer)
    return {"id": line["id"], "question": query, "answer": ans}


def main():
    q_path = "../../assets/question_d.json"
    result_path = "./result.json"
    result_json_list = []

    q_json_list = [json.loads(x.strip()) for x in open(q_path, "r", encoding="utf-8").readlines()]
    with cf.ProcessPoolExecutor(max_workers=70) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            result_json_list.append(future.result())

    result_json_list.sort(key=lambda x: x["id"])
    open(result_path, "w", encoding="utf-8").write(
        "\n".join([json.dumps(x, ensure_ascii=False) for x in result_json_list])
    )


if __name__ == "__main__":
    main()
