import requests
from zhipuai import ZhipuAI

import glm_tools
import net_request


def getanswer(comp_content):
    messages = [{"role": "user", "content": comp_content}]

    client = ZhipuAI(api_key="")
    tools = glm_tools.glmtools

    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.1,
    )
    print(response.choices[0].message)

    if response.choices[0].message.tool_calls is None:
        print("toolcallsnone")
        # 手动解析
        print(messages)
        print(response.choices[0].message.content)
        askcontent = response.choices[0].message.content
        try:
            apiname = askcontent.split("tool.")[1].split("(query_conds=")[0]
            apiquery_conds = askcontent.split("tool.")[1].split("(query_conds='")[1].split("', need_fields='")[0]
            api_need_fields = (
                askcontent.split("tool.")[1].split("(query_conds='")[1].split("', need_fields='")[1].split("')")[0]
            )
            print(f"apiname:{apiname},query:{apiquery_conds},needfiled:{api_need_fields}")
            print("...")
        except Exception:
            try:
                apiname = askcontent.split("tool.")[1].split("(need_fields=")[0]
                apiquery_conds = (
                    askcontent.split("tool.")[1].split("(need_fields='")[1].split("', query_conds='")[1].split("')")[0]
                )
                api_need_fields = askcontent.split("tool.")[1].split("(need_fields='")[1].split("', query_conds='")[0]
                print(f"apiname:{apiname},query:{apiquery_conds},needfiled:{api_need_fields}")
            except Exception as e:
                print(e)
                try:
                    apiname = askcontent.split("toolkit.")[1].split("(query_conds=")[0]
                    apiquery_conds = (
                        askcontent.split("toolkit.")[1].split("(query_conds='")[1].split("', need_fields='")[0]
                    )
                    api_need_fields = (
                        askcontent.split("toolkit.")[1]
                        .split("(query_conds='")[1]
                        .split("', need_fields='")[1]
                        .split("')")[0]
                    )
                    print(f"apiname:{apiname},query:{apiquery_conds},needfiled:{api_need_fields}")
                    print("...")
                except Exception as e:
                    print(e)
                    try:
                        apiname = askcontent.split("toolkit.")[1].split("(need_fields=")[0]
                        apiquery_conds = (
                            askcontent.split("toolkit.")[1]
                            .split("(need_fields='")[1]
                            .split("', query_conds='")[1]
                            .split("')")[0]
                        )
                        api_need_fields = (
                            askcontent.split("toolkit.")[1].split("(need_fields='")[1].split("', query_conds='")[0]
                        )
                        print(f"apiname:{apiname},query:{apiquery_conds},needfiled:{api_need_fields}")
                    except Exception as e:
                        answer = (
                            client.chat.completions.create(
                                model="glm-4",  # 填写需要调用的模型名称
                                messages=messages,
                                tools=tools,
                            )
                            .choices[0]
                            .message
                        )

                        return answer, str(e)

        func_name = apiname
        query_name = apiquery_conds.split(":")[0]
        query_content = apiquery_conds.split(":")[1]

        split_need_fields = api_need_fields.split(",")
        splited_need_fields = []
        for split_need_reduce in split_need_fields:
            splited_need_fields.append(split_need_reduce)

        rsp = net_request.net_getanswer(query_name, query_content, splited_need_fields, func_name)

        #
        # messages = [
        #     {
        #         "role": "user",
        #         "content": "我想要联系广州发展集团股份有限公司公司的法人代表，请问他的名字是什么？"
        #     }
        # ]
        messages.append(response.choices[0].message.model_dump())
        messages.append({"role": "tool", "content": f"{rsp.json()}"})
        answer1 = rsp.json()
        print(f"rspjson:{rsp.json()}")
        known_info = str(rsp.json())

        comp_content_new = f"""不要调用任何工具，已知的相关信息：{known_info}，整理已知信息中的相关信息回答问题，已知的信息就是需要回答问题的信息，不需要搜索，根据你的总结能力，回答问题：{comp_content}"""

        messages_new = [{"role": "user", "content": comp_content_new}]
        print("message_New")
        print(messages_new)

        client_new = ZhipuAI(api_key="")

        response_new = client_new.chat.completions.create(
            model="glm-4",  # 填写需要调用的模型名称
            messages=messages_new,
            temperature=0.1,
        )
        print(response_new.choices[0].message)

        # ,
        # "tool_call_id": response.choices[0].message.tool_calls[0].id

        answer = (
            client_new.chat.completions.create(
                model="glm-4",  # 填写需要调用的模型名称
                messages=messages_new,
            )
            .choices[0]
            .message
        )

        return answer, answer1
    else:
        print(response.choices[0].message.tool_calls[0])
        print("---")
        print(type(response.choices[0].message.tool_calls))

        # function = response.choices[0].message.tool_calls.function
        # func_args = function.arguments
        # func_name = function.name

        # 注意这里会返回公司名称的空内容

        function = response.choices[0].message.tool_calls[0].function
        func_args = function.arguments.replace("=", ":")
        func_name = function.name
        print(func_name)
        print(func_args)
        print(type(func_args))
        try:
            need_fields = eval(func_args)["need_fields"]
            query_conds = eval(func_args)["query_conds"]
        except Exception:
            print("loadquery_conds failed")
            need_fields = ""
            query_conds = "公司名称:无"

        # transfunc=func_args.split('"query_conds":"')[1].split('"}')[0].split(':')

        split_need_fields = need_fields.split(",")
        splited_need_fields = []
        for split_need_reduce in split_need_fields:
            splited_need_fields.append(split_need_reduce)
        print(need_fields)
        print(query_conds)
        transfunc = query_conds.split(":")
        query_name = transfunc[0]
        try:
            query_content = transfunc[1]
        except Exception as e:
            try:
                print(e)
                transfunc = query_conds.split("：")
                query_name = transfunc[0]
                query_content = transfunc[1]
            except Exception as e:
                print(e)
                answer = (
                    client.chat.completions.create(
                        model="glm-4",  # 填写需要调用的模型名称
                        messages=messages,
                        tools=tools,
                    )
                    .choices[0]
                    .message
                )
                answer1 = ""

                return answer, answer1

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

        #
        # messages = [
        #     {
        #         "role": "user",
        #         "content": "我想要联系广州发展集团股份有限公司公司的法人代表，请问他的名字是什么？"
        #     }
        # ]
        messages.append(response.choices[0].message.model_dump())
        messages.append(
            {
                "role": "tool",
                "content": f"{rsp.json()}",
                "tool_call_id": response.choices[0].message.tool_calls[0].id,
            }
        )

        answer = (
            client.chat.completions.create(
                model="glm-4",  # 填写需要调用的模型名称
                messages=messages,
                tools=tools,
            )
            .choices[0]
            .message
        )
        answer1 = ""

        return answer, answer1
