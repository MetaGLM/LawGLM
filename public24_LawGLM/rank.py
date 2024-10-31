import json

# 读取文件并逐行解析JSON对象
with open('/app/result_cashe.json', 'r', encoding='utf-8') as file:
    data = [json.loads(line) for line in file]

# 根据"id"字段排序
sorted_data = sorted(data, key=lambda x: x['id'])

# 将排序后的数据写入新文件，每行一个JSON对象
with open('/app/result.json', 'w', encoding='utf-8') as file:
    for item in sorted_data:
        file.write(json.dumps(item, ensure_ascii=False) + '\n')

print("排序完成，结果保存在result.json文件中。")
