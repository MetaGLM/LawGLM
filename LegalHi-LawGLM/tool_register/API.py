"""
Author: lihaitao
Date: 2024-08-04 18:31:16
LastEditors: Do not edit
LastEditTime: 2024-08-04 18:31:16
FilePath: /GLM2024/submit-image-demo/app/tool_register/API.py
"""

import requests


def API(api_name, args):
    domain = "comm.chatglm.cn"
    url = f"https://{domain}/law_api/s1_b/{api_name}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 5DC959180ACBFF13D363AFFEB38F81CE3AFD8BA74746FBB1",
    }
    flag = 0
    for k in args:
        if k == "need_fields":
            flag = 1
            # print(args[k])
            if type(args[k]) != list:
                args[k] = args[k]["Items"]
    if flag == 0:
        args["need_fields"] = []
    rsp = requests.post(url, json=args, headers=headers)
    return rsp.json()
