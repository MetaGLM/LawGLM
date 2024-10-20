export default interface ISubCompanyInfo {
    公司名称?: string;
    关联上市公司股票代码?: string;
    关联上市公司股票简称?: string;
    关联上市公司全称?: string;
    上市公司关系?: string;
    上市公司参股比例?: string;
    上市公司投资金额?: string;

    // 仅为模型知识增强使用（不代表母公司==上市公司）
    母公司参股比例?: string;
    母公司投资金额?: string;
}