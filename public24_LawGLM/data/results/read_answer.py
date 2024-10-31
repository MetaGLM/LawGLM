import json 

data_file = '/public/zzy/competition/B_Board/data/results/public24点燃心海_result_0710_new.json'
with open(data_file, 'r') as f: 
    data = f.readlines()

for item in data:
    print(json.loads(f))