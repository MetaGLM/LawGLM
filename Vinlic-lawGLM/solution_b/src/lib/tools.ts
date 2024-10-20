import _ from 'lodash';

import IMessage from "./interfaces/IMessage.ts";
import { MessageType } from "@/lib/enums.ts";
import ICompanyInfo from './interfaces/ICompanyInfo.ts';
import ICompanyRegister from './interfaces/ICompanyRegister.ts';
import ISubCompanyInfo from './interfaces/ISubCompanyInfo.ts';
import ILegalDocument from './interfaces/ILegalDocument.ts';
import api from './api.ts';
import logger from './logger.ts';

// 可用工具
const TOOLS = {
    getCompanyInfoTextByCompanyName,
    getCompanyInfoTextByStockCode,
    getCompanyInfoTextByRegisterCode,
    getCompanyInfoListTextByIndustry,
    getSubCompanyInfoListTextByCompanyName,
    getSubCompanyInfoTextBySubCompanyName,
    getParentCompanyInfoTextBySubCompanyName,
    getLegalDocumentTextByCaseNum,
    getLegalDocumentListTextByReason,
    getLegalDocumentListTextByPlaintiff,
    getLegalDocumentListTextByDefendant,
    calculate
};

/**
 * 工具调用分发
 * 
 * @param name 工具名称
 * @param args 参数对象
 */
async function toolCallDistribution(name: string, args: any = {}, messageCallback: (msg: IMessage) => void) {
    logger.info(`[调用工具${name}]`, args)
    if(Object.keys(args).length == 0) {
        logger.error(`[调用工具${name}时未提供任何参数]`);
        return `调用工具${name}必须提供合法的参数，请检查重试。`;
    }
    if(!TOOLS[name]) {
        logger.error(`[未找到${name}工具]`);
        return `工具${name}未找到，请检查工具名称重试。`;
    }
    const result = await TOOLS[name](args, messageCallback);
    logger.success(`[工具${name}调用成功]`)
    return result;
}

/**
 * 根据公司名称获取公司信息文本
 * 
 * @returns 公司信息文本
 */
async function getCompanyInfoTextByCompanyName({ companyName }, messageCallback: (msg: IMessage) => void) {
    let info = await api.getCompanyInfoByCompanyName(companyName, messageCallback);
    if(!info)
        return `未找到${companyName}的公司信息，请检查后重试。`;
    info = companyInfoFilter(info, ['公司名称']);
    let text = `已查找到${companyName}的公司信息：\n\n`;
    for(let key in info)
        text += `${key}：${info[key] || '无数据'}\n`
    text += `\n以上信息不包含母公司信息，如需母公司信息可以调用getParentCompanyInfoTextBySubCompanyName工具获取。`;
    return text;
}

/**
 * 根据股票代码获取公司信息文本
 * 
 * @returns 公司信息文本
 */
async function getCompanyInfoTextByStockCode({ stockCode }, messageCallback: (msg: IMessage) => void) {
    let info = await api.getCompanyInfoByStockCode(stockCode, messageCallback);
    if(!info)
        return `未找到公司代码（股票代码）为${stockCode}的公司信息，请检查后重试。`;
    info = companyInfoFilter(info);
    let text = `已查找到公司代码（股票代码）为${stockCode}的公司信息：\n\n`;
    for(let key in info)
        text += `${key}：${info[key] || '无数据'}\n`
    return text;
}

/**
 * 根据注册号获取公司信息文本
 *
 * @returns 公司信息文本
 */
async function getCompanyInfoTextByRegisterCode({ registerCode }, messageCallback: (msg: IMessage) => void) {
    let info = await api.getCompanyInfoByRegisterCode(registerCode, messageCallback);
    if(!info)
        return `未找到注册号为${registerCode}的公司信息`;
    info = companyInfoFilter(info, ['注册号']);
    let text = `已查找到注册号为${registerCode}的公司信息：\n\n`;
    for(let key in info)
        text += `${key}：${info[key] || '无数据'}\n`
    return text;
}

/**
 * 根据所属行业名称获取公司信息列表文本
 * 
 * @returns 公司信息列表文本
 */
async function getCompanyInfoListTextByIndustry({ industry }, messageCallback: (msg: IMessage) => void) {
    const infos = await api.getCompanyInfoListTextByIndustry(industry, messageCallback);
    if(!infos.length)
        return `未找到归属行业为${industry}的公司信息列表，请检查后重试。`;
    let text = '';
    // let text = `已查找到归属行业为${industry}的公司信息列表（共${infos.length}家）：\n\n`;
    infos.sort((a, b) => amountParse(b['注册资本']) - amountParse(a['注册资本']));
    // for(let i = 0;i < infos.length;i++) {
    //     const info = companyInfoFilter(infos[i], ['所属行业']);
    //     text += `${i + 1}.${info['公司名称'] || '未知公司'}\n`
    //     delete info['公司名称'];
    //     for(let key in info) {
    //         if(key == '上市公司参股比例')
    //             info[key] = info[key] ? `${parseInt(info[key])}%` : '无数据';
    //         text += `   ${key}：${info[key] || '无数据'}\n`
    //     }
    //     text += '\n';
    // }
    text += `所属行业为${industry}的子公司共有${infos.length}家，注册资本前3的公司为：` + infos.slice(0, 3).map(v => `${v['公司名称']}（${v['注册资本'] ? v['注册资本'] + '万元' :'无数据'}）`).join('、');
    return text;
}

/**
 * 根据母公司全称或股票简称获取所有子公司信息文本
 * 
 * @returns 所有子公司信息文本
 */
async function getSubCompanyInfoListTextByCompanyName({ companyName, excessInvestmentAmount, isHolding, isWhollyOwned }, messageCallback: (msg: IMessage) => void) {
    let infos = await api.getSubCompanyInfoListByCompanyName(companyName, messageCallback);
    if(!infos.length)
        return `未找到归属于${companyName}的子公司信息列表，也许你提供的是一家子公司名称，你可以尝试调用getParentCompanyInfoTextBySubCompanyName获取其母公司信息，请重试。`;
    const totalCount = infos.length;
    // 母公司向子公司的总投资金额
    const totalInvestmentAmount = infos.reduce((total, v) => Math.ceil(total + amountParse(v['上市公司投资金额'])), 0)
    // 子公司列表内容
    const listContent = '| 公司名称 | 参股比例 | 投资金额 |\n| --- | --- | --- |\n' + infos.reduce((str, v) => str += `| ${v['公司名称']} | ${v['上市公司参股比例'] ? v['上市公司参股比例'] + '%' : '无数据'} | ${v['上市公司投资金额'] || '无数据'} |\n`, '');
    // 子公司最高参股比例
    let maxShareholdingRatio = 0;
    // 最高参股比例子公司名称列表
    let maxShareholdingCompanyNames = [];
    // 控股子公司列表（参股比例50%以上）
    let holdingInfos = [];
    if(isHolding) {
        holdingInfos = infos.filter(v => {
            const ratio = Number(v['上市公司参股比例']) || 0;
            if(ratio > maxShareholdingRatio) {
                maxShareholdingRatio = ratio;
                maxShareholdingCompanyNames = []
            }
            if(ratio == maxShareholdingRatio)
                maxShareholdingCompanyNames.push(v['公司名称']);
            return ratio > 50;
        });
    }
    // 全资子公司列表（参股比例100%）
    let whollyOwnedInfos = [];
    if(isWhollyOwned) {
        whollyOwnedInfos = infos.filter(v => {
            const ratio = Number(v['上市公司参股比例']) || 0;
            return ratio == 100;
        });
    }
    // 子公司最高投资金额
    let maxInvestmentAmount = 0;
    // 最高投资金额的子公司名称列表
    let maxInvestmentAmountCompanyNames = [];
    // 超出投资金额子公司列表（超过指定投资金额）
    let excessInvestmentAmountInfos = [];
    const _excessInvestmentAmount = amountParse(excessInvestmentAmount || '0');
    const targetInfos = (isHolding ? holdingInfos : (isWhollyOwned ? whollyOwnedInfos : infos));
    excessInvestmentAmountInfos = targetInfos.filter(v => {
        const amount = amountParse(v['上市公司投资金额']);
        if(amount > maxInvestmentAmount) {
            maxInvestmentAmount = amount;
            maxInvestmentAmountCompanyNames = []
        }
        if(amount == maxInvestmentAmount)
            maxInvestmentAmountCompanyNames.push(v['公司名称']);
        return amount > _excessInvestmentAmount;
    });
    return [
        listContent,
        `以上是${companyName}的子公司列表，共有${totalCount}家，投资的总金额为${totalInvestmentAmount}人民币;`,
        `参股比例超过50%的${isHolding ? '控股' : ''}子公司有${holdingInfos.length}家` + (isWhollyOwned ? `，其中全资子公司有${whollyOwnedInfos.length}家;` : ';'),
        excessInvestmentAmount ? `${isHolding || isWhollyOwned ? '其中，' : ''}投资金额超过${excessInvestmentAmount}的有${excessInvestmentAmountInfos.length}家;` : '',
        `${isHolding ? '控股子公司中' : '子公司中'}参股比例最高的有：${maxShareholdingCompanyNames.join('、')}; 参股比例最高达到${maxShareholdingRatio.toFixed(2)}%;`,
        `${isHolding ? '控股子公司中' : '子公司中'}投资金额最高的有：${maxInvestmentAmountCompanyNames.join('、')}; 投资金额最高达到${Math.ceil(maxInvestmentAmount)}人民币。`,
    ].join('\n')
}

/**
 * 根据子公司名称获取子公司信息文本
 * 
 * @returns 子公司信息文本
 */
async function getSubCompanyInfoTextBySubCompanyName({ subCompanyName }, messageCallback: (msg: IMessage) => void) {
    let info = await api.getSubCompanyInfoBySubCompanyName(subCompanyName, messageCallback);
    if(!info)
        return `未找到${subCompanyName}信息`;
    info = subCompanyInfoFilter(info, ['公司名称']);
    let text = `已查找到该${subCompanyName}信息：\n\n`;
    for(let key in info)
        text += `${key}：${info[key] || '无数据'}\n`
    return text;
}

/**
 * 根据子公司名称获取母公司信息文本
 * 
 * @returns 子公司信息文本
 */
async function getParentCompanyInfoTextBySubCompanyName({ subCompanyName }, messageCallback: (msg: IMessage) => void) {
    const info = await api.getSubCompanyInfoBySubCompanyName(subCompanyName, messageCallback);
    if(!info)
        return '未找到该子公司信息，无法获得关联母公司信息';
    const parentCompanyName = info['关联上市公司全称'] || info['关联上市公司股票简称'];
    let parentInfo = await api.getCompanyInfoByCompanyName(parentCompanyName, messageCallback);
    parentInfo = companyInfoFilter(parentInfo);
    let text = `已查找到${subCompanyName}的母公司信息：\n\n`;
    for(let key in parentInfo)
        text += `${key}：${parentInfo[key] || '无数据'}\n`
    text += `\n${subCompanyName}是${parentInfo['公司名称']}的子公司`
    return text;
}

/**
 * 根据案号获取法律文书内容文本
 *
 * @returns 法律文书内容文本
 */
async function getLegalDocumentTextByCaseNum({ caseNum }, messageCallback: (msg: IMessage) => void) {
    let doc = await api.getLegalDocumentByCaseNum(caseNum, messageCallback);
    if(!doc)
        return `未找到案号为${caseNum}的历史法律文书，有可能缺失括号，请检查后重试。`;
    doc = legalDocumentFilter(doc, ['案号']);
    let text = `已查找到案号为${caseNum}的历史法律文书：\n\n`;
    for(let key in doc)
        text += `${key}：${doc[key] || '无数据'}\n`
    return text;
}

/**
 * 根据案由获取法律文书内容文本
 *
 * @returns 法律文书内容文本
 */
async function getLegalDocumentListTextByReason({ reason }, messageCallback: (msg: IMessage) => void) {
    const docs = await api.getLegalDocumentListByReason(reason, messageCallback);
    if (!docs.length)
        return `未找到案由为${reason}的历史法律文书内容列表，可能为0件。`;
    let text = `已查找到案由为${reason}的历史法律文书列表（共${docs.length}件）：\n\n`;
    for (let i = 0; i < docs.length; i++) {
        const doc = legalDocumentFilter(docs[i], ['案由']);
        text += `${i + 1}.${doc['标题'] || '未知案件'}\n`
        delete doc['标题'];
        for (let key in doc) {
            text += `   ${key}：${doc[key] || '无数据'}\n`
        }
        text += '\n';
    }
    text += `\n以上${docs.length}件法律文书案件的案由都是${reason}`
    return text;
}

/**
 * 根据原告获取法律文书内容文本
 *
 * @returns 法律文书内容文本
 */
async function getLegalDocumentListTextByPlaintiff({ plaintiff }, messageCallback: (msg: IMessage) => void) {
    const docs = await api.getLegalDocumentListByPlaintiff(plaintiff, messageCallback);
    if (!docs.length)
        return `未找到原告为${plaintiff}的历史法律文书内容列表，请检查后重试。`;
    let text = `已查找到原告为${plaintiff}的历史法律文书内容列表（共${docs.length}件）：\n\n`;
    const lawOfficeCounts = {};
    for (let i = 0; i < docs.length; i++) {
        const doc = legalDocumentFilter(docs[i], ['原告']);
        text += `${i + 1}.${doc['标题'] || '未知案件'}\n`
        delete doc['标题'];
        if(doc['原告律师']) {
            // 提取律师事务所列表
            const lawOffices = lawOfficesExtract(doc['原告律师']);
            lawOffices.forEach(name => lawOfficeCounts[name] ? lawOfficeCounts[name]++ : (lawOfficeCounts[name] = 1));
        }
        for (let key in doc) {
            text += `   ${key}：${doc[key] || '无数据'}\n`
        }
        text += '\n';
    }
    const lawOfficesDetail = Object.entries(lawOfficeCounts).reduce((str, v) => str + `${v[0]}：${v[1]}次\n`, '');
    text += `\n${plaintiff}是以上${docs.length}件法律文书案件的原告。` + (lawOfficesDetail ? `\n原告合作的事务所频次如下：\n${lawOfficesDetail}。` : '原告没有和律师事务所合作，合作次数为0。')
    return text;
}

/**
 * 根据被告获取法律文书内容文本
 *
 * @returns 法律文书内容文本
 */
async function getLegalDocumentListTextByDefendant({ defendant }, messageCallback: (msg: IMessage) => void) {
    const docs = await api.getLegalDocumentListByDefendant(defendant, messageCallback);
    if (!docs)
        return `未找到被告为${defendant}的法律文书，请检查后重试。`;
    if (!docs.length)
        return `未找到被告为${defendant}的历史法律文书内容列表，请检查后重试。`;
    let text = `已查找到被告为${defendant}的历史法律文书内容列表（共${docs.length}件）：\n\n`;
    const lawOfficeCounts = {};
    for (let i = 0; i < docs.length; i++) {
        const doc = legalDocumentFilter(docs[i], ['被告']);
        text += `${i + 1}.${doc['标题'] || '未知案件'}\n`
        delete doc['标题'];
        if(doc['被告律师']) {
            // 提取律师事务所列表
            const lawOffices = lawOfficesExtract(doc['被告律师']);
            lawOffices.forEach(name => lawOfficeCounts[name] ? lawOfficeCounts[name]++ : (lawOfficeCounts[name] = 1));
        }
        for (let key in doc) {
            text += `   ${key}：${doc[key] || '无数据'}\n`
        }
        text += '\n';
    }
    const lawOfficesDetail = Object.entries(lawOfficeCounts).reduce((str, v) => str + `${v[0]}：${v[1]}次\n`, '');
    text += `\n${defendant}是以上${docs.length}件法律文书案件的被告。` + (lawOfficesDetail ? `\nb被告合作的事务所频次如下：\n${lawOfficesDetail}。` : '被告没有和律师事务所合作，合作次数为0。');
    return text;
}

/**
 * 公司基本信息清理，减少与任务无关的干扰信息
 * 
 * @param info 公司基本信息对象
 * @param fields 扩展过滤字段列表
 */
function companyInfoFilter(info: ICompanyInfo, fields: string[] = []) {
    info = _.omit(info, [
        '关联证券',
        '公司代码',
        '所属市场',
        '官方网址',
        '入选指数',
        '经营范围',
        '机构简介',
        '每股面值',
        ...fields
    ]);
    return companyRegisterFilter(info);
}

/**
 * 公司注册信息清理，减少与任务无关的干扰信息
 * 
 * @param register 公司注册信息对象
 * @param fields 扩展过滤字段列表
 */
function companyRegisterFilter(register: ICompanyRegister, fields: string[] = []) {
    return _.omit(register, [
        '参保人数',
        '省份',
        '城市',
        '区县',
        ...fields
    ]);
}

/**
 * 子公司基本信息清理，减少与任务无关的干扰信息
 * 
 * @param info 子公司基本信息对象
 * @param fields 扩展过滤字段列表
 */
function subCompanyInfoFilter(info: ISubCompanyInfo, fields: string[] = []) {
    info['母公司参股比例'] = info['上市公司参股比例'];
    info['母公司投资金额'] = info['上市公司投资金额'];
    return _.omit(info, [
        '关联上市公司股票代码',
        '上市公司关系',
        '上市公司参股比例',
        '上市公司投资金额',
        ...fields
    ]);
}

/**
 * 法律文书内容清理，减少与任务无关的干扰信息
 * 
 * @param doc 法律文书对象对象
 * @param fields 扩展过滤字段列表
 */
function legalDocumentFilter(doc: ILegalDocument, fields: string[] = []) {
    return _.omit(doc, [
        '文书类型',
        '文件名',
        '判决结果',
        ...fields
    ]);
}

/**
 * 金额转换为数字
 * 
 * @param text 内容
 */
function amountParse(text: string) {
    if(!text)
        return 0;
    if(_.isFinite(text))
        return Number(text);
    text = text.replace(/\>|\<|\=|\,|\，/g, '');
    let times = 1;
    if(text.includes('亿'))
        times = 100000000;
    else if(text.includes('千万'))
        times = 10000000;
    else if(text.includes('万'))
        times = 10000;
    return parseFloat(text) * times;
}

/**
 * 律师事务所提取
 * 
 * @param text 内容
 */
function lawOfficesExtract(text: string) {
    const match = text.match(/,(.+?律师事务所)/g);
    if(!match)
        return [];
    return match.map(v => v.replace(/^,\s*/, '').trim());
}

function calculate({ nums }) {
    console.log(nums);
    return nums.reduce((total, num) => total + amountParse(num), 0);
}

export default {
    toolCallDistribution,
    ...TOOLS
}