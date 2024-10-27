# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 10:41:39 2024

@author: 86187
"""

tools_all = [
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "根据上市公司名称、公司简称、公司代码查找上市公司信息。通过公司简称查询公司名称",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": ["公司名称", "公司简称", "公司代码"],
                        "description": "查询信息字段名，公司名称如上海妙可蓝多食品科技股份有限公司,公司简称如妙可蓝多,'公司代码'如'600882'",
                    },
                    "value": {"type": "string", "description": "查询信息字段值"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "公司名称",
                                "公司简称",
                                "英文名称",
                                "关联证券",
                                "公司代码",
                                "曾用简称",
                                "所属市场",
                                "所属行业",
                                "成立日期",
                                "上市日期",
                                "法人代表",
                                "总经理",
                                "董秘",
                                "邮政编码",
                                "注册地址",
                                "办公地址",
                                "联系电话",
                                "传真",
                                "官方网址",
                                "电子邮箱",
                                "入选指数",
                                "主营业务",
                                "经营范围",
                                "机构简介",
                                "每股面值",
                                "首发价格",
                                "首发募资净额",
                                "首发主承销商",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_register",
            "description": "根据公司名称查询工商信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "需要查询的公司名称。公司名称如上海妙可蓝多食品科技股份有限公司。",
                    },
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "登记状态",
                                "统一社会信用代码",
                                "法定代表人",
                                "注册资本",
                                "成立日期",
                                "企业地址",
                                "联系电话",
                                "联系邮箱",
                                "注册号",
                                "组织机构代码",
                                "参保人数",
                                "行业一级",
                                "行业二级",
                                "行业三级",
                                "曾用名",
                                "企业简介",
                                "经营范围",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_register_name",
            "description": "根据统一社会信用代码查询公司全称（公司名称）。统一社会信用代码如91370000164102345T",
            "parameters": {
                "type": "object",
                "properties": {
                    "credit_code": {"type": "string", "description": "统一社会信用代码，如'91370000164102345T'"},
                },
                "required": ["credit_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sub_company_info",
            "description": "根据被投资的子公司名称获得投资该公司的母公司、投资比例、投资金额信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "需要查询的子公司名称。"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["关联上市公司全称", "上市公司关系", "上市公司参股比例", "上市公司投资金额"],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sub_company_info_list",
            "description": "根据上市公司（母公司）的名称查询该公司投资的所有子公司信息列表。通过公司名称查询子公司名称。参数only_wholly_owned为True返回全资(圈资)子公司",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_company_name": {"type": "string", "description": "需要查询的上市公司（母公司）的名称。"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "关联上市公司全称",
                                "上市公司关系",
                                "上市公司参股比例",
                                "上市公司投资金额",
                                "公司名称",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                    "only_wholly_owned": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否只返回全资子公司信息。",
                    },
                    "investment_amount_above": {
                        "type": "number",
                        "default": 0.0,
                        "description": "筛选投资金额大于等于该值的子公司。",
                    },
                },
                "required": ["parent_company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_document",
            "description": "根据案号查询裁判文书相关信息,根据案号查询原告律师事务所名称，根据案号查询被告律师事务所名称。案号格式如(2019)川01民初1949号,当查询被申请人时就是查询被告。",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_number": {"type": "string", "description": "需要查询的案号。如(2019)川01民初1949号"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "关联公司",
                                "原告",
                                "被告",
                                "原告律师事务所",
                                "被告律师事务所",
                                "案由",
                                "涉案金额",
                                "判决结果",
                                "日期",
                                "文件名",
                                "标题",
                                "文书类型",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段，注意原告就是上诉人、起诉人，日期字段就代表审理日期，当查询被申请人时就是查询被告。",
                        "include_judgment_result": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否需要判决结果字段信息。",
                        },
                    },
                    "additionalProperties": False,
                },
                "required": ["case_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_document_list",
            "description": "根据公司名称裁判文书信息，根据公司名称查询案号,涉案金额,原告, 被告, 原告律师事务所, 被告律师事务所, 案由, 判决结果等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "related_company": {"type": "string", "description": "需要查询的关联公司名称。"},
                    "role": {
                        "type": "string",
                        "enum": ["原告", "被告"],
                        "default": None,
                        "description": "查询公司作为被告、原告或两者(None)的角色，默认为'None'。",
                    },
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "关联公司",
                                "标题",
                                "案号",
                                "文书类型",
                                "原告",
                                "被告",
                                "原告律师事务所",
                                "被告律师事务所",
                                "案由",
                                "涉案金额",
                                "判决结果",
                                "审理日期",
                                "案件发生年度",
                                "文件名",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["related_company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_court_info",
            "description": "根据法院名称查找法院名录相关信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "court_name": {"type": "string", "description": "需要查询的法院名称。法院名称为全称"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["法院负责人", "成立日期", "法院地址", "法院联系电话", "法院官网"],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。注意区县、区县区划代码的区分",
                    },
                },
                "required": ["court_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_court_code",
            "description": "根据法院名称、法院代字、案号查询法院相关信息。根据案号查询法院名称等信息;通过案号查询审理法院名称",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": ["法院名称", "法院代字", "案号"],
                        "description": "查询信息字段名,法院名称如最高人民法院、北京市高级人民法院、北京市第一中级人民法院、北京市石景山区人民法院，法院代字如最高法、京、京01、京0107",
                    },
                    "value": {
                        "type": "string",
                        "description": "查询信息字段值,法院名称如最高人民法院、北京市高级人民法院、北京市第一中级人民法院、北京市石景山区人民法院，法院代字如最高法、京、京01、京0107",
                    },
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["法院名称", "行政级别", "法院级别", "法院代字", "区划代码", "级别"],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。注意区县、区县区划代码的区分",
                    },
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lawfirm_info_log",
            "description": "通过律师事务所名称查询律师事务所信息，如根据通过律师事务所名称查询律师事务所地址等",
            "parameters": {
                "type": "object",
                "properties": {
                    "lawfirm_name": {"type": "string", "description": "需要查询的律师事务所名称。"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "律师事务所唯一编码",
                                "律师事务所负责人",
                                "事务所注册资本",
                                "事务所成立日期",
                                "律师事务所地址",
                                "通讯电话",
                                "通讯邮箱",
                                "律所登记机关",
                                "业务量排名",
                                "服务已上市公司",
                                "报告期间所服务上市公司违规事件",
                                "报告期所服务上市公司接受立案调查",
                            ],
                        },
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["lawfirm_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_address_info",
            "description": "根据地址查询对应的省份城市区县信息",
            "parameters": {
                "type": "object",  # 类型
                "properties": {  # 字段
                    "address": {
                        "type": "string",
                        "description": "需要查询的地址信息。地址如：上海市闵行区新骏环路138号1幢401室",
                    },
                    # "date": {"type": "string", "description": "日期,如2020年1月1日"},
                    "need_fields": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["省份", "城市", "区县"]},
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_address_code",
            "description": "根据省份、城市、区县查询对应的区划代码。",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string", "description": "省份,如北京市"},
                    "city": {"type": "string", "description": "城市,如北京市"},
                    "district": {"type": "string", "description": "区县,如海淀区"},
                    "need_fields": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["城市区划代码", "区县区划代码"]},
                    },
                },
                "required": ["province", "city", "district"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_temp_info",
            "description": "根据日期、省份、城市查询对应的天气相关信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {"type": "string", "description": "省份,如北京市，如山东省"},
                    "city": {"type": "string", "description": "城市，如北京市"},
                    "date": {"type": "string", "description": "日期，特别注意格式要传入正确，如2020年1月1日"},
                    "need_fields": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["天气", "最高温度", "最低温度", "湿度"]},
                    },
                },
                "required": ["province", "city", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_abstract",
            "description": "根据案号查询对应的法律文档文本摘要。",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_number": {"type": "string", "description": "案号,如(2019)川01民初1949号"},
                    "need_fields": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["文本摘要"]},
                        "description": "需要返回的字段列表，如果为None则返回所有字段。",
                    },
                },
                "required": ["case_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_xzgxf_info",
            "description": "根据案号查询对应的限制高消费相关信息。案号格式如(2019)川01民初1949号",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_number": {"type": "string", "description": "案号,如(2019)川01民初1949号"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "限制高消费企业名称",
                                "法定代表人",
                                "申请人",
                                "涉案金额",
                                "执行法院",
                                "立案日期",
                                "限高发布日期",
                            ],
                            "description": "需要返回的字段列表，如果为None则返回所有字段。",
                        },
                    },
                },
                "required": ["案号"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_xzgxf_info_list",
            "description": "根据企业名称查询对应的所有限制高消费相关信息列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "需要查询的限制高消费企业名称"},
                    "need_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "案号",
                                "法定代表人",
                                "申请人",
                                "涉案金额",
                                "执行法院",
                                "立案日期",
                                "限高发布日期",
                            ],
                        },
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_company",
            "description": "根据公司名称判断是否为上市公司",
            "parameters": {
                "type": "object",
                "properties": {"company_name": {"type": "string", "description": "需要查询判断的公司名称。"}},
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "func8",
            "description": "根据公司名称查询某个公司子公司数量及投资总额,根据公司名称查询旗下多少家子公司,投资总额是多少",
            "parameters": {
                "type": "object",
                "properties": {"company_name": {"type": "string", "description": "公司名称"}},
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "function_11",
            "description": "根据公司名称查询案件信息，查询某公司在某年是否被起诉，以及涉案总额；通过公司名称查询的涉案次数、涉案金额；通过公司名称查询某公司作为被起诉人（被告）、原告的涉案次数、涉案金额，及相关案号；查询一下某某公司参与的案件有涉案金额的有哪些？涉案金额总和为？ 可以直接优先调用。当要求使用function_11查询时请尝试强制调用该工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "需要查询的公司名称。"},
                    "role": {
                        "type": "string",
                        "enum": ["defendant", "plaintiff", "both"],
                        "default": "both",
                        "description": "查询公司作为被告(defendant)、原告(plaintiff)或两者(both)的角色，默认为'both'。查询被起诉次数时应该使用defendant",
                    },
                    "year": {
                        "type": "integer",
                        "minimum": 1900,
                        "maximum": 2100,
                        "description": "指定查询的年份，如果不提供，则查询所有年份的数据。",
                    },
                    "cause": {
                        "type": "string",
                        "enum": ["劳务及劳务者纠纷", "劳动合同纠纷", "合同相关纠纷", "财产损害"],
                        "description": "特定的案由，如'劳务及劳务者纠纷'、'劳动合同纠纷','合同相关纠纷'等，如果不提供，则不按案由过滤。",
                    },
                    "amount_range": {
                        "type": "array",
                        "items": [{"type": "number"}, {"type": "number"}],
                        "description": "指定的金额区间，如[0, 10000]，表示查询涉案金额在该区间内的案件。注意当查询有涉案金额的条件可以设置[0.0001,1000000000000000]",
                    },
                    "phase": {
                        "type": "string",
                        "enum": ["民事初审", "民事终审", "执行保全财政", "执行"],
                        "default": None,
                        "description": "审理阶段，如民事初审, 民事终审等，默认为'None'",
                    },
                },
                "required": ["company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_companies_by_capital",
            "description": "根据母公司名称和指定的排名类型或特定排名位置，通过公司名称查询特定条件子公司名称、投资金额。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "母公司名称，用于查找其下属子公司。"},
                    "rank_type": {
                        "type": "string",
                        "enum": ["最高", "前3", "特定排名"],
                        "default": "特定排名",
                        "description": "排序类型，可选值包括：'最高'（返回投资额最大的子公司）、'前3'（返回投资额最高的前三名子公司）或'特定排名'（需配合使用rank_position）。",
                    },
                    "rank_position": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "当rank_type为'特定排名'时，此参数有效，指定了需要获取的子公司的排名位置。",
                    },
                },
                "required": ["company_name", "rank_type"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_restriction_and_max_amount",
            "description": "根据企业名称判断对应的公司是否被限制高消费，并返回涉及的最大金额及相应案号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "目标企业的名称，用于查询其是否有高消费限制的记录。",
                    }
                },
                "required": ["company_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total_amount_and_count_simple",
            "description": "根据公司名称查询限制高消费(限高)的总次数以及涉案总金额。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "需要查询公司名称，用于查询限制高消费(限高)的总次数以及涉案总金额。",
                    }
                },
                "required": ["company_name"],
                "additionalProperties": False,
            },
            "returns": {
                "type": "object",
                "description": "返回一个对象，包含两项：\n- '总涉案金额': 涉案金额的总和（金额类型）。\n- '总记录次数': 总次数",
                "properties": {
                    "总涉案金额": {"type": "number", "description": "涉案金额的汇总。"},
                    "总记录次数": {"type": "integer", "description": "涉案次数总计数。"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_highest_legal_document_by_companyname",
            "description": "获取指定公司的最高涉案金额的法律文件信息。可以查询最高涉案金额的案号, 文书类型, 原告, 被告, 原告律师事务所, 被告律师事务所, 案由, 涉案金额, 判决结果,审理日期, 案件发生年度等 查询涉案金额最高的案件信息时优先使用此功能",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "公司的名称，用于查询该公司的法律文件列表。"},
                    "role": {
                        "type": "string",
                        "enum": ["原告", "被告"],
                        "default": None,
                        "description": "查询公司作为被告、原告或两者(None)的角色，默认为'None'。",
                    },
                    "n": {
                        "type": "integer",
                        "description": "第几高，1代表最高第一高,2代表第二高,3代表第三高，-1代表最低",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
]
