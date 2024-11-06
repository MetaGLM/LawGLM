import requests


def net_getanswer(query_name, query_content, splited_need_fields, func_name):
    passfunc = {
        "query_conds": {query_name: query_content},
        "need_fields": splited_need_fields,
    }
    print("passfunc:")
    print(passfunc)
    domain = "comm.chatglm.cn"

    headers = {"Content-Type": "application/json", "Authorization": "Bearer "}

    url = f"https://{domain}/law_api/s1_b/{func_name}"
    print(url)

    rsp = requests.post(url, json=passfunc, headers=headers)
    print(rsp.json())
    return rsp
