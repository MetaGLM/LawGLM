glmtools = [
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": '实现的功能：根据上市公司名称、简称或代码查找上市公司信息。告诉我已知的信息，包括在以下任何一项里：【公司名称;公司简称;英文名称;关联证券;公司代码;曾用简称;所属市场;所属行业;成立日期;上市日期;法人代表;总经理;董秘;邮政编码;注册地址;办公地址;联系电话;传真;官方网址;电子邮箱;入选指数;入选指数;经营范围;机构简介;每股面值;首发价格;首发募资净额;首发主承销商】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "公司名称:公司", "need_fields": "法人代表,公司简称"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_register",
            "description": '实现的功能：根据统一社会信用代码查询公司名称，类似【"query_conds": "统一社会信用代码:913305007490121183", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sub_company_info",
            "description": '实现的功能：根据被投资的子公司名称获得投资该公司的上市公司、投资比例、投资金额等信息,类似【"query_conds": "公司名称:公司", "need_fields": "    "】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sub_company_info_list",
            "description": '实现的功能：根据上市公司（母公司）的名称查询该公司投资的所有子公司信息list。告诉我已知的信息，包括在以下任何一项里：【关联上市公司全称;上市公司关系;上市公司参股比例;上市公司投资金额;公司名称;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "关联上市公司全称:上海航天汽车机电股份有限公司", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_document",
            "description": '实现的功能：根据案号查询裁判文书相关信息，并返回对应项的名称和需要调用的信息，类似【"query_conds": "案号:(2019)沪0115民初61975号", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_document_list",
            "description": '实现的功能：根据关联公司查询所有裁判文书相关信息list。告诉我已知的信息，包括在以下任何一项里：【关联公司;标题;案号;文书类型;原告;被告;原告律师事务所;被告律师事务所;案由;涉案金额;判决结果;日期;文件名;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "关联公司:上海爱斯达克汽车空调系统有限公司", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_court_info",
            "description": '实现的功能：根据法院名称查询法院名录相关信息。告诉我已知的信息，包括在以下任何一项里：【法院名称;法院负责人;成立日期;法院地址;法院联系电话;法院官网;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "法院名称:上海市浦东新区人民法院", "need_fields": "法院地址"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_court_code",
            "description": '实现的功能：根据法院名称或者法院代字查询法院代字等相关数据。告诉我已知的信息，包括在以下任何一项里：【法院名称;行政级别;法院级别;法院代字;区划代码;级别;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "法院名称:上海市浦东新区人民法院", "need_fields": "行政级别"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lawfirm_info",
            "description": '实现的功能：根据律师事务所查询律师事务所名录。告诉我已知的信息，包括在以下任何一项里：【律师事务所名称;律师事务所唯一编码;律师事务所负责人;事务所注册资本;事务所成立日期;律师事务所地址;通讯电话;通讯邮箱;律所登记机关;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "律师事务所名称:爱德律师事务所", "need_fields": "通讯邮箱"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lawfirm_log",
            "description": '实现的功能：根据律师事务所查询律师事务所统计数据。告诉我已知的信息，包括在以下任何一项里：【律师事务所名称;业务量排名;服务已上市公司;报告期间所服务上市公司违规事件;报告期所服务上市公司接受立案调查;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "律师事务所名称:北京市金杜律师事务所", "need_fields": "业务量排名"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_address_info",
            "description": '实现的功能：根据地址查该地址对应的省份城市区县。告诉我已知的信息，包括在以下任何一项里：【地址; 省份;城市;区县;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "地址:西藏自治区那曲地区安多县帕那镇中路13号", "need_fields": "城市"】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_address_code",
            "description": '实现的功能：根据省市区查询区划代码。告诉我已知的信息，包括在以下任何一项里：【省份;城市;城市区划代码;区县;区县区划代码;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "省份:西藏自治区,城市:拉萨市,区县:城关区", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_temp_info",
            "description": '实现的功能：根据日期及省份城市查询天气相关信息。告诉我已知的信息，包括在以下任何一项里：【日期;省份;城市;天气;最高温度;最低温度;湿度;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "省份:北京市,城市:北京市,日期:2020年1月1日", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_legal_abstract",
            "description": '实现的功能：根据案号查询文本摘要。告诉我已知的信息，包括在以下任何一项里：【文件名;案号;文本摘要;】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "案号:（2019）沪0115民初61975号", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_xzgxf_info",
            "description": '实现的功能：根据案号查询限制高消费相关信息。告诉我已知的信息，包括在以下任何一项里：【限制高消费企业名称;案号;法定代表人;申请人;涉案金额;执行法院;立案日期;限高发布日期】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "案号:（2018）鲁0403执1281号", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_xzgxf_info_list",
            "description": '实现的功能：根据企业名称查询所有限制高消费相关信息list。告诉我已知的信息，包括在以下任何一项里：【限制高消费企业名称;案号;法定代表人;申请人;涉案金额;执行法院;立案日期;限高发布日期】，并返回对应项的名称和需要调用的信息，类似【"query_conds": "限制高消费企业名称:欣水源生态环境科技有限公司", "need_fields": ""】',
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sum",
            "description": "实现的功能：求和，可以对传入的int、float、str数组进行求和，str数组只能转换字符串里的千万亿",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank",
            "description": "实现的功能：排序接口，返回按照values排序的keys。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_conds": {
                        "type": "string",
                        "description": "已知信息的key-value格式",
                    },
                    "need_fields": {
                        "type": "string",
                        "description": "需要的信息，list格式",
                    },
                },
                "required": ["query_conds", "need_fields"],
            },
        },
    },
    {"type": "web_search", "web_search": {"enable": False}},
]
