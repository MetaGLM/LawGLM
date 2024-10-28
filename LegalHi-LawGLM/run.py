"""
Author: lihaitao
Date: 2024-07-29 12:02:55
LastEditors: Do not edit
LastEditTime: 2024-08-07 10:23:00
FilePath: /GLM2024/submit-image-demo/app/run.py
#"""

import concurrent.futures as cf
import json
from main import run, run_all


def main():
    q_path = "../assets/question_d.json"
    result_path = "/app/result.json"
    result_json_list = []

    q_json_list = [json.loads(x.strip()) for x in open(q_path, "r", encoding="utf-8").readlines()]
    with cf.ProcessPoolExecutor(max_workers=50) as executor:
        future_list = [executor.submit(run, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            result_json_list.append(future.result())
    result_json_list.sort(key=lambda x: x["id"])
    open(result_path, "w", encoding="utf-8").write(
        "\n".join([json.dumps(x, ensure_ascii=False) for x in result_json_list])
    )


if __name__ == "__main__":
    main()
