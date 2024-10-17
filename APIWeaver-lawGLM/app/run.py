from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from run_with_process import process_question

PATH = '/tcdata/question_d.json'
RESULT = '/app/result.json'


def main():
    with open(PATH, encoding='utf8') as f:
        questions = [json.loads(line) for line in f]
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_question, question) for question in questions]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
    return results


if __name__ == '__main__':
    # import json
    with open(RESULT, 'w', encoding='utf8') as fw:
        pass
    with open(PATH, encoding='utf8') as f:
        for i in f:
            data = json.loads(i)
            data['answer'] = ''
            with open(RESULT, 'a', encoding='utf8') as fw:
                fw.write(json.dumps(data, ensure_ascii=False))
                fw.write('\n')
    results = main()
    import time

    time.sleep(1)
    print(results)
    if len(results) == 200:
        print('开始写入...')
        with open(RESULT, 'w', encoding='utf8') as fw:
            fw.write('\n'.join([json.dumps(i, ensure_ascii=False) for i in results]))
    else:
        print('长度不匹配')
    time.sleep(1)
    print('写入完成')
