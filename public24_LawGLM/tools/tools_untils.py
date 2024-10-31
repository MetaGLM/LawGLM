import re 
import json 
from tools.tool_correction_info import * 
from services.all_tools_service_register import *



def find_company_info(i):
    services = [
        (get_listed_company_info_service, "的上市基本信息已找到"),
        (get_company_register_service, "的工商信息已找到"),
        (get_company_involved_cases_info_service, "的涉案信息已找到"),
        (get_company_xzgxf_by_company_name_service, "的制高消费案件相关信息已找到"),
        (get_parent_company_info_by_child_company_name_service, "的母公司信息已找到"),
        (get_listed_sub_company_info_service_by_parent_company_name, "的子公司信息已找到"),
        (get_listed_all_sub_company_info_service_by_parent_company_name, "的全资子公司信息已找到"),
        (get_company_info_service_by_abbreviation,"的公司全称已找到")
    ]
    for service, message in services:
        try:
            result = service(i)
            if result.empty==False:
                return f"{i}{message}"
        except Exception as e:
            continue
    return f"{i}的信息未找到"

def find_lawfirm_info(i):
    services = [
        (get_lawfirm_info_service, "的律所信息已找到"),
        (get_lawfirm_business_service, "的业务情况统计数据已找到")
    ]
    for service, message in services:
        try:
            result = service(i)
            if result.empty==False:
                return f"{i}{message}"
        except Exception as e:
            continue
    return f"{i}的信息未找到"

def find_court_info(i):
    services = [
        (get_court_info_service, "的法院信息已找到"),
        (get_court_code_service, "的法院级别和代号等相关数据已找到")
    ]
    
    for service, message in services:
        try:
            result = service(i)
            if result.empty==False:
                return f"{i}{message}"
        except Exception as e:
            continue
    return f"{i}的信息未找到"

def find_code_info(i):
    services = [
        (get_company_info_service_by_code, f"公司代码(公司股票代码){i}的公司全称已找到"),
        (get_company_name_by_uniform_social_code_service, f"统一社会信用代码{i}的公司全称已找到")
    ]
    for service, message in services:
        try:
            result = service(i)
            if result.empty==False:
                return message
        except Exception as e:
            continue
    return f"{i}的信息未找到"        

def find_reference_info(i):

    services = [
        (get_legal_document_service, "的裁判文书已找到"),
        (get_legal_abstract_by_reference_service, "的文本摘要已找到"),
        (get_xzgxf_info_by_reference_service, "的制高消费案件相关信息已找到")
    ]
    
    for service, message in services:
        try:
            result = service(i)
            if result.empty==False:
                return f"{i}{message}"
        except Exception as e:
            continue
    return f"{i}的信息未找到"



def tool_error_info(tool_name):
        ###检查为空的情况
        correction_info = ""
        if tool_name== "get_company_register_service":
            correction_info = "查询公司的工商信息查询结果为空，表示查询公司未上市，请使用get_company_info_service查询公司基本信息。"
        if 'company' in tool_name:
            correction_info = correction_mapping['company']
        elif 'court' in tool_name:
            correction_info = correction_mapping['court']
        elif 'address' in tool_name or "temp" in tool_name:
            correction_info = correction_mapping['address']
        elif 'reference' in tool_name or 'legal' in tool_name:
            correction_info = correction_mapping['reference']
        else:
            correction_info = correction_mapping['default']
            
        return correction_info


def check_and_edit_observation(tool_name, obs):
        ###检查为空的情况
        correction_info = ""
        correction_flag = False
        if "[]" in obs in obs:
            correction_flag = True 
            if tool_name== "get_company_register_service":
                correction_info = "查询公司的工商信息查询结果为空，表示查询公司未上市，请使用get_company_info_service查询公司基本信息。"
            if 'company' in tool_name:
                correction_info = correction_mapping['company']
            elif 'court' in tool_name:
                correction_info = correction_mapping['court']
            elif 'address' in tool_name or "temp" in tool_name:
                correction_info = correction_mapping['address']
            elif 'reference' in tool_name or 'legal' in tool_name:
                correction_info = correction_mapping['reference']
            else:
                correction_info = correction_mapping['default']
        elif "has no attribute" in obs:
            correction_flag = True  
            correction_info = obs  +  attribution_mapping[tool_name]
        elif "Traceback" in obs:
            correction_flag = True
            correction_info = obs
        else:
            correction_info = obs
            
        return correction_flag, correction_info


def parse_tool_call(raw_str):
        '''
            解析工具调用
        '''
        def clean_item(item):
            item = item.strip()
            item = item.replace(" ", "")
            item = item.replace("\'", "")
            item = item.replace("`", "")
            item = item.replace("\"", "")
            item = item.replace("\n", "")
            item = item.replace("[", "")
            item = item.replace("]", "")
            item = item.replace("{", "")
            item = item.replace("}", "")
            item = item.replace(" ", "")
            
            return item

        cleaned_str = raw_str.replace("`", "").replace("\n", "")
        splits = cleaned_str.split("python")
        func_name = splits[0].strip()
        args_str =  splits[1].strip()
        
        pattern_small_bracket = r"[\()](.*)[\)]"
        pattern_large_bracket = r"\{(.*?)\}"
        matches1 = re.search(pattern_small_bracket, args_str)
        matches2 = re.search(pattern_large_bracket, args_str)
        args = []
        if matches1:
            list_content = matches1.group(1)
            # 将字符串转换为列表
            args = [item.strip().strip("\'").strip() for item in list_content.split(",")]
        elif matches2:
            dict_content = matches2.group(1)
            # 将字符串转换为字典
            args = [item.strip().strip("\'").strip() for item in dict_content.split(",")]
        elif "[" in  args_str:
            args_str = clean_item(args_str)
            args = [item.strip().strip("\'").strip() for item in args_str.split(",")]
        else:
            args_str = clean_item(args_str)
            args_str = args_str.replace("tool.", "\n").strip("")
            if "\n" in args_str:
                args = args_str.split("\n")
            elif "," in args_str:
                args = args_str.split(",")
            else:
                args = [args_str]
        print(args)
        args_dict = {}
        if len(args) != 0:
            list_str = ""
            for k, arg in enumerate(args):
                
                if "=" not in arg and ":" not in arg :
                    if  '['  in arg or k == len(args) - 1:
                        list_str = list_str + arg 
                        print(list_str)
                        key, value = list_str.split("=")
                        args_dict[clean_item(key)] = clean_item(value)
                        list_str = ""
                        continue 
                    if list_str != ""  :
                        list_str = list_str + arg + ","
                        continue 
                
                if "=" in arg :
                    if list_str != "":
                        key, value = list_str.split("=")
                        args_dict[clean_item(key)] = clean_item(value)
                    list_str = ""
                    if "need_fields" in arg  and  k != len(args) - 1:
                        list_str = list_str + arg + ","
                    else:
                        key, value = arg.split("=")

                        args_dict[clean_item(key)] = clean_item(value)
                elif ":" in arg:
                    if list_str != "":
                        key, value = list_str.split("=")
                        args_dict[clean_item(key)] = clean_item(value)
                    list_str = ""
                    if "need_fields" in arg and  k != len(args) - 1: 
                        key, value = arg.split(":")
                        list_str = key + '=' + value + ',' 
                    else:
                        key, value = arg.split(":")
                        args_dict[clean_item(key)] = clean_item(value)
                
        
        args_dict_str = json.dumps(args_dict, ensure_ascii=False)
        return  func_name, args_dict_str