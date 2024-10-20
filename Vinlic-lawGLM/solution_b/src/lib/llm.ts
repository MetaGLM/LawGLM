import OpenAI from 'openai';
import _ from 'lodash';

import config from './config.ts';
import logger from './logger.ts';

const MODEL = config.zhipuai.model || 'glm-4-0520';
const ENDPOINT = config.zhipuai.endpoint;
const API_KEY = config.zhipuai.api_key;
const MAX_TOKENS = config.zhipuai.max_tokens;

const client = new OpenAI({
    baseURL: ENDPOINT,
    apiKey: API_KEY
})

/**
 * 问题分类
 */
async function questionClassify(question: string, categorys: any[], usageCallback?: (tokens: number) => void) {
    logger.info(`[正在分类问题] ${question}`);
    const categorysDescription = categorys.reduce((str, v) => str + `${v[0]}：${v[1]}\n`, '');
    const result = await chatCompletions([
        {
            "role": "system",
            "content": `你是一个法律问题分类助手，需要根据用户输入判断它属于以下哪一个分类：\n${categorysDescription}\n请直接输出分类名称，不需要解释。\n通常只需要一个分类，除非问题明确涉及多个分类才提供多个，请使用英文逗号隔开它们。`
            // "content": `你是一个法律问题分类助手，需要根据用户输入判断它属于以下哪一个分类，如果问题明确涉及多个分类请使用英文逗号隔开：\n[${categorys.join(',')}]`
        },
        {
            "role": "user",
            "content": `问题：${question}\n\n分类：`
        
        }
    ], usageCallback);
    const choices = [];
    for(let v of categorys) {
        if(result.includes(v[0]))
            choices.push(v[0]);
    }
    if(choices.length == 0)
        logger.error(`[此问题无法判断分类] ${question}`);
    else
        logger.success(`[问题分类完成] ${choices.join('、')}`);
    return choices;
}

/**
 * 咨询法律概念
 * 
 * @param question 问题内容
 */
async function consultingLegalConcept(question: string, history: OpenAI.ChatCompletionToolMessageParam[] = [], afterContent = '', usageCallback?: (tokens: number) => void) {
    logger.info(`[正在咨询法律条文] ${question}`);
    const result = await toolCalls([
        {
            "role": "system",
            "content": `你是一个法律条文答题助手，需要根据用户提供的问题，精确完整的提供一份标准的答案，不需要输出提示语和注意事项，任何题目都需要作答，如果数据为0也请如实回答。`
        },
        ...history,
        {
            "role": "user",
            "content": `请精确完整的回答此问题：${question}\n${afterContent}\n\n答案：`
        }
    ], [], usageCallback);
    logger.success(`[法律条文咨询完成]`);
    return result;
}

/**
 * 咨询公司信息
 * 
 * @param question 问题内容
 */
async function consultingCompanyInfo(question: string, history: OpenAI.ChatCompletionToolMessageParam[] = [], afterContent = '', disableToolNames: string[] = [], usageCallback?: (tokens: number) => void) {
    logger.info(`[正在咨询公司信息] ${question}`);
    const result = await toolCalls([
        {
            "role": "system",
            "content": `你是一个公司信息答题助手，你能够调用工具查询一家或多家公司的基本信息、注册信息、行业信息、子公司信息、子公司的母公司信息等来精准完整的提供你的答案。\n不需要输出提示语和注意事项。`
        },
        ...history,
        {
            "role": "user",
            "content": `\n请精确完整的回答此问题：${question}\n\n如果上文存在未查询到的数据你可以继续调用工具\n${afterContent}\n\n答案：`
        }
    ], [
        {
            "type": "function",
            "function": {
                "name": "getCompanyInfoTextByCompanyName",
                "description": "根据提供的公司名称或简称或英文名称，查询该公司的基本信息和注册信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "companyName": {
                            "type": "string",
                            "description": "公司名称或简称或英文名称",
                        }
                    },
                    "required": ["companyName"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getCompanyInfoTextByRegisterCode",
                "description": "根据提供的公司注册号，查询该公司的基本信息和注册信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "registerCode": {
                            "type": "string",
                            "description": "公司注册号",
                        }
                    },
                    "required": ["registerCode"],
                },
            }
        },
        // {
        //     "type": "function",
        //     "function": {
        //         "name": "getCompanyInfoTextByStockCode",
        //         "description": "根据提供的公司代码（股票代码）查询该公司的基本信息和注册信息",
        //         "parameters": {
        //             "type": "object",
        //             "properties": {
        //                 "stockCode": {
        //                     "type": "string",
        //                     "description": "公司代码（股票代码）",
        //                 }
        //             },
        //             "required": ["stockCode"],
        //         },
        //     }
        // },
        {
            "type": "function",
            "function": {
                "name": "getCompanyInfoListTextByIndustry",
                "description": "查询所属该行业的公司列表，根据提供的行业名称，可以获得包含每家公司的基本信息和注册信息列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {
                            "type": "string",
                            "description": "行业名称",
                        }
                    },
                    "required": ["industry"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getParentCompanyInfoTextBySubCompanyName",
                "description": "查询母公司的信息，根据提供的子公司名称查询母公司或控股公司的公司信息，方便获取子公司属于哪个公司旗下。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subCompanyName": {
                            "type": "string",
                            "description": "子公司名称",
                        }
                    },
                    "required": ["subCompanyName"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getSubCompanyInfoListTextByCompanyName",
                "description": "查询子公司信息列表，根据提供的公司名称或简称或英文名称，可以获得该公司的所有子公司信息列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "companyName": {
                            "type": "string",
                            "description": "公司名称",
                        },
                        "excessInvestmentAmount": {
                            "type": "string",
                            "description": "母公司投资子公司超过的金额，包含单位（如5000万）"
                        },
                        "isHolding": {
                            "type": "boolean",
                            "description": "是否查询控股公司（参股比例超过50%的公司）"
                        },
                        "isWhollyOwned": {
                            "type": "boolean",
                            "description": "是否查询全资子公司（参股比例为100%的公司）"
                        }
                    },
                    "required": ["companyName", "isHolding", "isWhollyOwned"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getSubCompanyInfoTextBySubCompanyName",
                "description": "根据子公司名称查询子公司的信息，可以查询子公司关联的母公司名称和母公司对该子公司的投资金额、参股比例、控股情况等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subCompanyName": {
                            "type": "string",
                            "description": "子公司名称",
                        }
                    },
                    "required": ["subCompanyName"],
                },
            }
        },
        // {
        //     "type": "function",
        //     "function": {
        //         "name": "calculate",
        //         "description": "加法计算器，可用于统计总投资金额，单位是元。",
        //         "parameters": {
        //             "type": "object",
        //             "properties": {
        //                 "nums": {
        //                     "type": "array",
        //                     "description": "金额列表",
        //                 }
        //             },
        //             "required": ["nums"],
        //         },
        //     }
        // }
    ].filter(f => !disableToolNames.includes(f.function.name)) as OpenAI.Chat.Completions.ChatCompletionTool[], usageCallback);
    logger.success(`[公司信息咨询完成]`);
    return result;
}

/**
 * 咨询法律文书
 * 
 * @param question 问题内容
 */
async function consultingLegalDocument(question: string, history: OpenAI.ChatCompletionToolMessageParam[] = [], afterContent = '', disableToolNames: string[] = [], usageCallback?: (tokens: number) => void) {
    logger.info(`[正在咨询法律文书] ${question}`);
    const result = await toolCalls([
        {
            "role": "system",
            "content": `你是一个法律文书答题助手，你能够调用工具根据案号等信息查询相应法律文书的内容或判决的法律条文依据等，并根据题目要求，精确完整的提供一份标准的答案，不需要输出提示语和注意事项。`
        },
        ...history,
        {
            "role": "user",
            "content": `\n请精确完整的回答此问题：${question}\n\n如果上文存在未查询到的数据你可以继续调用工具\n${afterContent}\n\n答案：`
        }
    ], [
        {
            "type": "function",
            "function": {
                "name": "getLegalDocumentTextByCaseNum",
                "description": "根据提供的案号查询该法律文书或查询判决的法律条文依据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "caseNum": {
                            "type": "string",
                            "description": "案号",
                        }
                    },
                    "required": ["caseNum"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getLegalDocumentListTextByReason",
                "description": "根据提供的案由，查询该案由的法律文书列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "案由",
                        }
                    },
                    "required": ["reason"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getLegalDocumentListTextByPlaintiff",
                "description": "根据提供的原告，查询出现该原告的法律文书列表，面临诉讼时公司将是原告",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plaintiff": {
                            "type": "string",
                            "description": "原告名称",
                        }
                    },
                    "required": ["plaintiff"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "getLegalDocumentListTextByDefendant",
                "description": "根据提供的被告，查询出现该被告的法律文书列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "defendant": {
                            "type": "string",
                            "description": "被告名称",
                        }
                    },
                    "required": ["defendant"],
                },
            }
        }
    ].filter(f => !disableToolNames.includes(f.function.name)) as OpenAI.Chat.Completions.ChatCompletionTool[], usageCallback);
    logger.success(`[法律文书咨询完成]`);
    return result;
}

/**
 * 检查任务是否完成
 * 
 * @param question 问题内容
 * @param answer 答案内容
 */
async function checkTaskCompleted(question: string, answer: string, history: OpenAI.ChatCompletionToolMessageParam[] = [], rounds: number, usageCallback?: (tokens: number) => void) {
    if(!answer)
        return { completed: false, explain: '' }
    logger.info(`[正在检查任务是否已完成] 第${rounds}轮`);
    const result = await chatCompletions([
        ...history,
        {
            "role": "user",
            "content": `问题：帮我查一下健帆生物科技集团股份有限公司的行业归属，并告知该行业内的企业总数是多少？\n回答：健帆生物科技集团股份有限公司的行业归属是专用设备制造业，该行业内的企业总数为62家。\n\n完整度：100%\n已完成：yes\n待补充信息：无\n\n以上是任务检查样例。\n\n你是一个任务完成状态检查助手，你不需要关注答案正确率，仅从答题完整性入手，你会先评估并输出一个完整度，当完整度高于50%时再是否完成位置输出“yes”，否则在是否完成位置输出“no”并在待补充信息位置提供答案缺失的信息。\n\n示例输出：\n完整度：{完整度}\n已完成：{是否完成}\n待补充信息：{待补充信息或无}\n\n，只需关注是否有某些数据没有查询到或数值不明确。\n\n问题：${question}。\n回答：${answer}。`
        }
    ], usageCallback, 'glm-4-0520');
    const completed = result.toLowerCase().includes('yes');
    completed ? logger.success(`[任务已完成] 第${rounds}轮`) : logger.warn(`[任务未完成，即将重试] 第${rounds}轮`);
    return {
        completed,
        explain: result
    };
}

/**
 * 信息抽取
 * 
 * @param question 问题内容
 * @param content 数据内容
 */
async function infoExtract(question: string, content: string, usageCallback?: (tokens: number) => void) {
    logger.info('[正在抽取信息]');
    let result = await chatCompletions([
        {
            "role": "system",
            "content": "你是一个参考内容关键信息提取助手，你的目标是提取和题目相关的信息但不改写不缩写信息内容。\n从提供的参考内容中提取与题目相关的信息并完整列出，你不需要回答题目，不能缺失题目需要的关键信息。"
        },
        {
            "role": "user",
            "content": `${content}\n\n以上为参考内容。\n\n题目：${question}。\n\n注意，你不需要回答题目，提取到的信息（如果部分信息未找到无需列出）：\n`
        }
    ], usageCallback);
    return result;
}

/**
 * 答案整理复述
 * 
 * @param question 问题内容
 * @param answer 答案内容
 */
async function answerRephrase(question: string, answer: string, usageCallback?: (tokens: number) => void) {
    logger.info('[正在总结复述答案]');
    let result = await chatCompletions([
        {
            "role": "system",
            "content": "Q: 我想了解重庆莱美药业股份有限公司的注册状况、企业类别以及成立日期。\nA: 重庆莱美药业股份有限公司的注册状况为存续，企业类别是股份有限公司（上市公司），成立日期为1999年09月06日。\n\nQ: 我想了解06865 福莱特玻璃这个股票代码的上市公司信息，可以提供公司的英文名称吗？\nA: 06865 福莱特玻璃股票代码的上市公司的英文名称是Flat Glass Group Co., Ltd.。\n\nQ: 我想了解化学原料和化学制品制造业这个行业的公司有哪些，请列出注册资本最大的3家头部公司，并给出他们的具体注册资本数额\nA: 在化学原料和化学制品制造业行业中，头部的3家公司分别是浙江龙盛集团股份有限公司, 阳煤化工股份有限公司, 北京海新能源科技股份有限公司，它们的注册资本分别为325333.186, 237598.1952, 234972.0302。\n\nQ: 上海家化联合股份有限公司为原告时他主要和哪家律师事务所合作?合作次数为几次。\nA: 上海家化联合股份有限公司主要和浙江若屈律师事务所律师合作，合作了11次。\n\n参考以上对话例子中Answer的回复风格, 重新复述(rephrase)以下问答中的A，注意:\n- 回答简要切题, 输出一行回答不换行，使用中文\n- 问题涉及的名词、关键词、英文、数字要完整填写，不缩写不改写信息，不能遗漏关键信息\n- 复述部分问题内容等"
        },
        {
            "role": "user",
            "content": `Q：${question}。\nA：${answer}（完整复述和列出内容）。\n\n直接提供答案完整复述，不缩写不改写，不允许省略公司名称等信息。以下是复述：`
        }
    ], usageCallback);
    result = result.replace(/Q(:|：).+\n*A(:|：)\s?/, '').replace(/A(:|：)\s?/, '').replace(/写\n/, '').replace(/^(,|，)/, '');
    return result;
}

/**
 * 日常沟通交流
 * 
 * @param question 问题内容
 */
async function communication(question: string, usageCallback?: (tokens: number) => void) {
    logger.info('[正在日常沟通交流]');
    const result = await chatCompletions([
        {
            "role": "system",
            "content": "你是一个专业的法律助手，名字是GLM法律顾问，需要严谨可靠的回答用户的任何问题。"
        },
        {
            "role": "user",
            "content": question
        }
    ], usageCallback);
    return result;
}

async function chatCompletions(messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[], usageCallback?: (tokens: number) => void, model?: string) {
    const response = await client.chat.completions.create({
        model: model || MODEL,
        messages,
        tools: [
            {
                "type": "web_search",
                "web_search": {
                    "enable": false
                }
            } as any
        ],
        tool_choice: "auto",
        max_tokens: MAX_TOKENS
    });
    if(!response.choices || !response.choices[0])
        throw new Error('LLM response error');
    if(usageCallback && response.usage && _.isFinite(response.usage.total_tokens))
        usageCallback(response.usage.total_tokens);
    return response.choices[0].message.content;
}

async function toolCalls(messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[], tools: OpenAI.Chat.Completions.ChatCompletionTool[] = [], usageCallback?: (tokens: number) => void, model?: string) {
    tools.push({
        "type": "web_search",
        "web_search": {
            "enable": false
        }
    } as any)
    const response = await client.chat.completions.create({
        model: model || MODEL,
        messages,
        tools,
        tool_choice: "auto",
        max_tokens: MAX_TOKENS
    });
    if(!response.choices || !response.choices[0])
        throw new Error('LLM response error');
    if(usageCallback && response.usage && _.isFinite(response.usage.total_tokens))
        usageCallback(response.usage.total_tokens);
    const callResults = response.choices[0].message.tool_calls || [];
    return {
        content: response.choices[0].message.content || null,
        calls: callResults.filter(v => v.type == 'function').map(v => {
            const { id, function: _function } = v;
            const { name, arguments: argsJson } = _function;
            const args = _.attempt(() => JSON.parse(argsJson));
            return {
                id,
                name,
                args: !_.isError(args) ? args : {}
            };
        })
    }
}

export default {
    questionClassify,
    consultingLegalConcept,
    consultingCompanyInfo,
    consultingLegalDocument,
    infoExtract,
    checkTaskCompleted,
    answerRephrase,
    communication
};