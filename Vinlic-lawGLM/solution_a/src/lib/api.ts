import axios from "axios";
import _ from "lodash";
import logger from "./logger.ts";

import IMessage from "./interfaces/IMessage.ts";
import { MessageType } from "@/lib/enums.ts";
import ICompanyInfo from "./interfaces/ICompanyInfo.ts";
import ICompanyRegister from "./interfaces/ICompanyRegister.ts";
import ISubCompanyInfo from "./interfaces/ISubCompanyInfo.ts";
import ILegalDocument from "./interfaces/ILegalDocument.ts";
import config from "./config.ts";

// 法律API
const LAW_API_ENDPOINT = config.law_api.endpoint;
const LAW_API_TOKEN = config.law_api.token;
const LAW_API_CONCURRENT = config.law_api.concurrent;

// 网络检索API
const WEB_SEARCH_MODEL = config.web_search.model;
const WEB_SEARCH_ENDPOINT = config.web_search.endpoint;
const WEB_SEARCH_TOKEN = config.web_search.token;

/**
 * 根据公司名称获取公司信息
 * 
 * @param companyName 公司名称
 * @returns 公司信息
 */
async function getCompanyInfoByCompanyName(companyName: string, messageCallback: (msg: IMessage) => void): Promise<(ICompanyInfo&ICompanyRegister)|null> {
    logger.info(`[正通过公司名称查询公司信息] ${companyName}`);
    const [
        info,
        register
    ] = await Promise.all([
        requestObj('/get_company_info', {
            company_name: companyName
        }, messageCallback),
        getCompanyRegisterByCompanyName(companyName, messageCallback)
    ]);
    if(info) {
        // 去除干扰项
        delete info['经营范围'];
        register ? logger.success(`[成功找到公司信息和注册信息] ${companyName}`) : logger.success(`[成功找到公司信息] ${companyName}`);
        return Object.assign(info, register);
    }
    const _companyName = (await Promise.all([
        searchCompanyNameByInfo({ '公司简称': companyName }, messageCallback),
        searchCompanyNameByInfo({ '英文名称': companyName }, messageCallback),
        searchCompanyNameByInfo({ '曾用简称': companyName }, messageCallback)
    ])).filter(v => v)[0];
    if(!_companyName) {
        register ? logger.success(`[未找到公司信息但找到注册信息] ${companyName}`) : logger.error(`[未找到此公司信息] ${companyName}`);
        return register;
    }
    const [_info, _register] = await Promise.all([
        requestObj('/get_company_info', {
            company_name: _companyName
        }, messageCallback),
        getCompanyRegisterByCompanyName(_companyName, messageCallback)
    ])
    if(_info) {
        // 去除干扰项
        delete _info['经营范围'];
        logger.success(`[成功找到公司信息] ${_companyName}`);
        return Object.assign(_info, _register || {});
    }
    if(!_register)
        logger.error(`[未找到此公司信息] ${_companyName}`);
    logger.success(`[成功找到公司信息] ${_companyName}`);
    return _register;
}

/**
 * 根据股票代码获取公司信息
 * 
 * @param stockCode 股票代码
 * @returns 公司信息
 */
async function getCompanyInfoByStockCode(stockCode: string, messageCallback: (msg: IMessage) => void): Promise<ICompanyInfo|null> {
    logger.info(`[正通过股票代码查询公司名称] ${stockCode}`);
    const companyName = await searchCompanyNameByInfo({ '公司代码': stockCode.trim() }, messageCallback);
    if(!companyName) {
        logger.error(`[未找到股票代码为${stockCode}的公司]`);
        return null;
    }
    const result = await getCompanyInfoByCompanyName(companyName, messageCallback);
    if(!result)
        logger.error(`[未找到股票代码为${stockCode}的公司]`);
    else
        logger.success(`[已找到股票代码为${stockCode}的公司] ${companyName}`);
    return result;
}

/**
 * 根据注册号获取公司信息
 * 
 * @param registerCode 注册号
 * @returns 公司信息
 */
async function getCompanyInfoByRegisterCode(registerCode: string, messageCallback: (msg: IMessage) => void): Promise<ICompanyInfo|null> {
    logger.info(`[正通过注册号查询公司名称] ${registerCode}`);
    const companyName = await searchCompanyNameByRegister({ '注册号': registerCode.trim() }, messageCallback);
    if(!companyName) {
        logger.error(`[未找到注册号为${registerCode}的公司]`);
        return null;
    }
    const result = await getCompanyInfoByCompanyName(companyName, messageCallback);
    if(!result)
        logger.error(`[未找到注册号为${registerCode}的公司]`);
    else
        logger.success(`[已找到注册号为${registerCode}的公司] ${companyName}`);
    return result;
}

/**
 * 根据所属行业名称获取公司信息列表
 * 
 * @param industry 行业名称
 * @returns 公司信息列表
 */
async function getCompanyInfoListTextByIndustry(industry: string, messageCallback: (msg: IMessage) => void): Promise<(ICompanyInfo&ICompanyRegister)[]> {
    logger.info(`[正通过所属行业查询公司名称] ${industry}`);
    const companyNames = await searchCompanyNamesByInfo({
        '所属行业': industry.trim()
    }, messageCallback);
    if(companyNames.length == 0) {
        logger.error(`[未找到归属${industry}行业的公司]`);
        return [];
    }
    let infos = [];
    let tasks = [];
    while(infos.length != companyNames.length) {
        const name = companyNames[infos.length + tasks.length];
        if(tasks.length < Math.min(LAW_API_CONCURRENT, companyNames.length - infos.length)) {
            tasks.push(getCompanyInfoByCompanyName(name, messageCallback));
            continue
        }
        infos = infos.concat((await Promise.all(tasks)).filter(v => v));
        tasks = [];
    }
    logger.success(`[已找到归属${industry}行业的公司] ${infos.length}家`);
    return infos;
}

/**
 * 根据公司基本信息某个字段是某个值来查询具体的公司名称
 * 
 * @param options 公司基本信息选项
 * @returns 公司名称列表
 */
async function searchCompanyNameByInfo(options: ICompanyInfo, messageCallback: (msg: IMessage) => void): Promise<string|null> {
    const result = await requestObj('/search_company_name_by_info', optionsConvert(options), messageCallback) as ICompanyInfo;
    if(!result)
        return null;
    return result['公司名称'];
}

/**
 * 根据公司基本信息某个字段是某个值来查询所有相关公司名称
 * 
 * @param options 公司基本信息选项
 * @returns 公司名称列表
 */
async function searchCompanyNamesByInfo(options: ICompanyInfo, messageCallback: (msg: IMessage) => void): Promise<string[]> {
    const list = await requestList('/search_company_name_by_info', optionsConvert(options), messageCallback) as ICompanyInfo[];
    return list.map(v => v['公司名称']);
}

/**
 * 根据公司名称获得该公司所有注册信息
 * 
 * @param companyName 公司名称
 * @returns 
 */
async function getCompanyRegisterByCompanyName(companyName: string, messageCallback: (msg: IMessage) => void): Promise<ICompanyRegister|null> {
    return await requestObj('/get_company_register', {
        company_name: companyName.trim()
    }, messageCallback);
}

/**
 * 根据公司注册信息某个字段是某个值来查询具体的公司名称
 * 
 * @param companyName 公司名称
 */
async function searchCompanyNameByRegister(options: ICompanyRegister, messageCallback: (msg: IMessage) => void): Promise<string> {
    const result = await requestObj('/search_company_name_by_register', optionsConvert(options), messageCallback);
    if(!result)
        return null;
    return result['公司名称'];
}

/**
 * 根据母公司全称或股票简称获取所有子公司信息
 * 
 * @param companyName 母公司名称
 */
async function getSubCompanyInfoListByCompanyName(companyName: string, messageCallback: (msg: IMessage) => void): Promise<ISubCompanyInfo[]> {
    logger.info(`[正通过母公司名称查询子公司信息] ${companyName}`);
    let subCompanyNames = (await Promise.all([
        searchSubCompanyNamesBySubInfo({ '关联上市公司全称': companyName }, messageCallback),
        searchSubCompanyNamesBySubInfo({ '关联上市公司股票简称': companyName }, messageCallback)
    ])).reduce((arr, v) => [...arr, ...v], []);
    if(subCompanyNames.length == 0) {
        const companyInfo = await getCompanyInfoByCompanyName(companyName, messageCallback);
        if(!companyInfo) {
            logger.error(`[未找到${companyName}的子公司]`);
            return [];
        }
        subCompanyNames = await searchSubCompanyNamesBySubInfo({ '关联上市公司全称': companyInfo['公司名称'] }, messageCallback);
        if(subCompanyNames.length == 0) {
            logger.error(`[未找到${companyName}的子公司]`);
            return [];
        }
    }
    let infos = [];
    let tasks = [];
    while(infos.length != subCompanyNames.length) {
        const name = subCompanyNames[infos.length + tasks.length];
        if(tasks.length < Math.min(LAW_API_CONCURRENT, subCompanyNames.length - infos.length)) {
            tasks.push(getSubCompanyInfoBySubCompanyName(name, messageCallback));
            continue
        }
        infos = infos.concat((await Promise.all(tasks)).filter(v => v));
        tasks = [];
    }
    logger.success(`[已找到${companyName}的子公司] ${infos.length}家`);
    return infos;
}

/**
 * 根据子公司名称获取子公司信息
 * 
 * @param subCompanyName 子公司名称
 */
async function getSubCompanyInfoBySubCompanyName(subCompanyName: string, messageCallback: (msg: IMessage) => void): Promise<ISubCompanyInfo|null> {
    logger.info(`[正通过子公司名称查询子公司信息] ${subCompanyName}`);
    const result = await requestObj('/get_sub_company_info', {
        company_name: subCompanyName.trim().trim()
    }, messageCallback);
    if(!result)
        logger.error(`[未找到此子公司信息] ${subCompanyName}`);
    else
        logger.success(`[已找到子公司信息] ${subCompanyName}`);
    return result;
}

/**
 * 根据子公司选项获取所有子公司名称
 * 
 * @param options 子公司选项
 */
async function searchSubCompanyNamesBySubInfo(options: ISubCompanyInfo, messageCallback: (msg: IMessage) => void): Promise<string[]> {
    const list = await requestList('/search_company_name_by_sub_info', optionsConvert(options), messageCallback);
    return list.map(v => v['公司名称']);
}

/**
 * 根据案号获取法律文书
 * 
 * @param caseNum 案号
 * @returns 法律文书信息
 */
async function getLegalDocumentByCaseNum(caseNum: string, messageCallback: (msg: IMessage) => void): Promise<ILegalDocument|null> {
    logger.info(`[正通过案号查询法律文书] ${caseNum}`);
    const result = await requestObj('/get_legal_document', {
        case_num: caseNum.trim().replace('（', '(').replace('）', ')')
    }, messageCallback);
    if(!result)
        logger.error(`[未找到案号${caseNum}的法律文书]`);
    else
        logger.success(`[已找到案号${caseNum}的法律文书]`);
    return result;
}

/**
 * 根据案由获取该案由的法律文书列表
 * 
 * @param reason 案由
 * @returns 法律文书列表
 */
async function getLegalDocumentListByReason(reason: string, messageCallback: (msg: IMessage) => void): Promise<ILegalDocument[]> {
    logger.info(`[正通过案由查询法律文书] ${reason}`);
    const caseNums = await searchCaseNumByLegalDocument({
        '案由': reason.trim()
    }, messageCallback);
    if(caseNums.length == 0) {
        logger.error(`[未找到案由为${reason}的法律文书]`);
        return [];
    }
    let docs = [];
    let tasks = [];
    while(docs.length != caseNums.length) {
        const caseNum = caseNums[docs.length + tasks.length];
        if(tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
            tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
            continue
        }
        docs = docs.concat((await Promise.all(tasks)).filter(v => v));
        tasks = [];
    }
    logger.success(`[已找到案由为${reason}的法律文书] ${docs.length}件`);
    return docs;
}

/**
 * 根据原告，获取该原告的法律文书列表
 * 
 * @param plaintiff 原告
 * @returns 法律文书列表
 */
async function getLegalDocumentListByPlaintiff(plaintiff: string, messageCallback: (msg: IMessage) => void): Promise<ILegalDocument[]> {
    logger.info(`[正通过原告查询法律文书] ${plaintiff}`);
    const caseNums = await searchCaseNumByLegalDocument({
        '原告': plaintiff.trim()
    }, messageCallback);
    if(caseNums.length == 0) {
        logger.error(`[未找到原告为${plaintiff}的法律文书]`);
        return [];
    }
    let docs = [];
    let tasks = [];
    while(docs.length != caseNums.length) {
        const caseNum = caseNums[docs.length + tasks.length];
        if(tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
            tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
            continue
        }
        docs = docs.concat((await Promise.all(tasks)).filter(v => v));
        tasks = [];
    }
    logger.success(`[已找到原告为${plaintiff}的法律文书] ${docs.length}件`);
    return docs;
}

/**
 * 根据被告，获取该被告的法律文书列表
 * 
 * @param defendant 被告
 * @returns 法律文书列表
 */
async function getLegalDocumentListByDefendant(defendant: string, messageCallback: (msg: IMessage) => void): Promise<ILegalDocument[]> {
    logger.info(`[正通过被告查询法律文书] ${defendant}`);
    const caseNums = await searchCaseNumByLegalDocument({
        '被告': defendant.trim()
    }, messageCallback);
    if(caseNums.length == 0) {
        logger.error(`[未找到被告为${defendant}的法律文书]`);
        return [];
    }
    let docs = [];
    let tasks = [];
    while(docs.length != caseNums.length) {
        const caseNum = caseNums[docs.length + tasks.length];
        if(tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
            tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
            continue
        }
        docs = docs.concat((await Promise.all(tasks)).filter(v => v));
        tasks = [];
    }
    logger.success(`[已找到被告为${defendant}的法律文书] ${docs.length}件`);
    return docs;
}

/**
 * 根据法律文书某个字段是某个值来查询具体的案号
 * 
 * @param options 法律文书选项
 * @returns 法律文书案号列表
 */
async function searchCaseNumByLegalDocument(options: ILegalDocument, messageCallback: (msg: IMessage) => void): Promise<string[]> {
    const list = await requestList('/search_case_num_by_legal_document', optionsConvert(options), messageCallback);
    return list.map(v => v['案号']);
}

/**
 * 选项转换
 * 
 * @param options 选项
 */
function optionsConvert(options: any) {
    let _options: any = {};
    for(let key in options) {
        _options.key = key;
        _options.value = options[key];
    }
    return _options;
}

/**
 * 请求对象
 * 
 * @param url 接口路径
 * @param data 请求数据
 */
async function requestObj(url: string, data = {}, messageCallback: (msg: IMessage) => void): Promise<Record<string, string>> {
    const result = await request(url, data, messageCallback);
    if(_.isArray(result)) {
        if(!result[0])
            return null;
        return result[0];
    }
    return result;
}

/**
 * 请求列表
 * 
 * @param url 接口路径
 * @param data 请求数据
 */
async function requestList(url: string, data = {}, messageCallback: (msg: IMessage) => void): Promise<Record<string, string>[]> {
    const result = await request(url, data, messageCallback);
    if(_.isArray(result))
        return result;
    return [];
}

/**
 * 请求法律API
 * 
 * @param url 接口路径
 * @param data 请求数据
 */
async function request(url: string, data = {}, messageCallback: (msg: IMessage) => void): Promise<Record<string, string>[]|Record<string, string>> {
    console.log(`[调用接口] ${url} ${JSON.stringify(data)}`);
    messageCallback({ type: MessageType.RequestAPI, title: '🌐 调用外部API', data: { method: 'POST', url, data } })
    const result = await axios.request({
        method: "POST",
        url: `${LAW_API_ENDPOINT}${url}`,
        data,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${LAW_API_TOKEN}`
        }
    });
    if(result.status != 200)
        throw new Error(`Request failed: [${result.status}]${result.statusText || 'Unknown'}`);
    messageCallback({ type: MessageType.RequestAPI, title: '🌐 调用外部API', data: result.data, finish: true })
    return result.data;
}

/**
 * 网络检索API
 * 
 * @param content 
 */
async function webSearch(content: string) {
    logger.info(`[正在网络检索] ${content}`);
    const result = await axios.request({
        method: "POST",
        url: `${WEB_SEARCH_ENDPOINT}/chat/completions`,
        data: {
            model: WEB_SEARCH_MODEL,
            messages: [
                {
                    "role": "user",
                    "content": `请检索问题并提供完整答案：${content}`
                }
            ]
        },
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${WEB_SEARCH_TOKEN}`
        }
    });
    if(result.status != 200)
        throw new Error(`Request failed: [${result.status}]${result.statusText || 'Unknown'}`);
    if(!result.data || !result.data.choices || !result.data.choices[0])
        throw new Error(`Request failed: [${result.data.code}]${result.data.message}`);
    logger.success(`[完成网络检索] ${content}`);
    return result.data.choices[0].message.content;
}

export default {
    getCompanyInfoByCompanyName,
    getCompanyInfoByStockCode,
    getCompanyInfoByRegisterCode,
    getCompanyInfoListTextByIndustry,
    getSubCompanyInfoListByCompanyName,
    getSubCompanyInfoBySubCompanyName,
    getLegalDocumentByCaseNum,
    getLegalDocumentListByReason,
    getLegalDocumentListByPlaintiff,
    getLegalDocumentListByDefendant,
    webSearch
};