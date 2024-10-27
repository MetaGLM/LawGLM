# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 07:22:58 2024

@author: 86187
"""

import tools

tools_list = tools.tools_all

for i in tools_list:
    d = {"function_name": i["function"]["name"], "description": i["function"]["description"]}

    print(d)
    try:
        d1 = {"输出的字段": i["function"]["parameters"]["properties"]["need_fields"]["items"]["enum"]}
        d.update(d1)
        #  print(d1)
        print(d)
    except KeyError:
        pass


LL = []
for i in tools_list:
    LL.append(i["function"]["name"])
print(LL)
