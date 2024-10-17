import re

with open('./knowledge/tools_txt.py', encoding='utf8') as f:
    chunks = re.split('\n\n\n+', f.read())

TOOLS_DESC = []

for i in chunks[1:]:
    pattern, function_doc, code = i.split('\n', 2)
    function_name = re.search(r'def\s+(\w+)\(', code).group(1)
    function_info = {'code': code,
                     'function_doc': function_doc,
                     'pattern': pattern[2:],
                     'function_name': function_name}
    TOOLS_DESC.append(function_info)

with open('./knowledge/tools.py', encoding='utf8') as f:
    chunks = re.split('\n\n\n+', f.read())

TOOLS = []

# print(len(chunks))
for i in chunks[1:]:
    pattern, function_doc, code = i.split('\n', 2)
    function_name = re.search(r'def\s+(\w+)\(', code).group(1)
    function_info = {'code': code,
                     'function_doc': function_doc,
                     'pattern': pattern[2:],
                     'function_name': function_name}
    TOOLS.append(function_info)
