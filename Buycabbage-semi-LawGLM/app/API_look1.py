from zhipuai import ZhipuAI
import json
import tools
import pandas as pd

client = ZhipuAI()

def glm4_create_air(max_attempts, messages):
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model="glm-4-0520",
            messages=messages,
        )
        if "```python" in response.choices[0].message.content:
            continue
        else:
            break
    return response


def API_look(question, tools):
    # Specify the file path
    file_path = "./API_look.txt"

    # Use a with statement to open the file
    with open(file_path, "r", encoding="utf-8") as file:
        content_p = file.read()

    # Construct the prompt
    prompt = content_p + f"我有上面这些API,我要回答{question},需要哪些function_name"
    # print(prompt)
    # print('------------------------')

    messages = [{"role": "user", "content": prompt}]
    response = glm4_create_air(1, messages)
    content = response.choices[0].message.content.strip()

    # Define the list of API functions
    api_list = [
        "get_company_info",
        "get_company_register",
        "get_company_register_name",
        "get_sub_company_info",
        "get_sub_company_info_list",
        "get_legal_document",
        "get_legal_document_list",
        "get_court_info",
        "get_court_code",
        "get_lawfirm_info_log",
        "get_address_info",
        "get_address_code",
        "get_temp_info",
        "get_legal_abstract",
        "get_xzgxf_info",
        "get_xzgxf_info_list",
        "check_company",
        "func8",
        "function_11",
        "get_top_companies_by_capital",
        "check_restriction_and_max_amount",
        "calculate_total_amount_and_count_simple",
        "get_highest_legal_document_by_companyname",
    ]

    # Filter the tools based on the API functions mentioned in the response
    api_list_filter = [api for api in api_list if api in content]
    filtered_tools = [tool for tool in tools if tool.get("function", {}).get("name") in api_list_filter]

    return content, api_list_filter, filtered_tools


if __name__ == "__main__":
    # Read lines from the JSON file
    lines = [line.strip() for line in open("../tcdata/question_c.json", "r", encoding="utf-8") if line.strip()]
    lines = lines[2:3]  # Select a specific subset of questions

    # Ensure that tools is a list of dictionaries
    if isinstance(tools.tools_all, list):
        tools_list = tools.tools_all
    else:
        raise ValueError("The 'tools' attribute must be a list of dictionaries.")

    def task(line):
        line = json.loads(line)
        query = line["question"]

        content, api_list_filter, filtered_tools = API_look(query, tools_list)
        print(filtered_tools)

        # Use the filtered tools for further processing
        # Assuming the 'answer' is the list of function names that were filtered
        # ans = [tool['function']['name'] for tool in filtered_tools]

        return {
            "id": line["id"],
            "question": query,
            "content": content,  # The original content is not returned by the task function
            "answer": filtered_tools,
            "api_list_filter": api_list_filter,
        }

    data = []
    for i in lines:
        data.append(task(i))

    # Write the data to an Excel file
    df = pd.DataFrame(data)
    df.to_excel("./API_look_3.xlsx", index=False)

    # Print the last processed line
    print(i)
