import json
import concurrent.futures as cf


def process_one(question_json):
    return question_json


def main():
    q_path = "./c_question.json"
    result_path = "./c_result.json"
    result_json_list = []

    q_json_list = [json.loads(x.strip()) for x in open(q_path, "r", encoding="utf-8").readlines()]
    with cf.ProcessPoolExecutor(max_workers=4) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            result_json_list.append(future.result())

    result_json_list.sort(key=lambda x: x["id"])
    open(result_path, "w", encoding="utf-8").write(
        "\n".join([json.dumps(x, ensure_ascii=False) for x in result_json_list])
    )


if __name__ == "__main__":
    main()
