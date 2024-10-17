import jieba
from rank_bm25 import BM25Okapi
import json
from fuzzywuzzy import fuzz


class CoderRecall:
    def __init__(self, code_list):
        self.code_list = code_list
        self.query_list = [i['function_doc'] for i in code_list]
        self.reload_bm25()

    def reload_bm25(self):
        tokenized_contents = [list(desc) for desc in self.query_list]
        # 创建BM25模型实例
        self.bm25 = BM25Okapi(tokenized_contents)
        self.code_dic = {i['function_doc']: i['code'] for i in self.code_list}

    def add_code(self, code_info):
        self.code_list.append(code_info)
        self.query_list.append(code_info['function_doc'])
        self.reload_bm25()

    def load(self, path):
        self.code_list = []
        with open(path, encoding='utf8') as f:
            for i in f:
                self.code_list.append(json.loads(i))

        self.query_list = [i['function_doc'] for i in self.code_list]
        tokenized_contents = [list(desc) for desc in self.code_dic.keys()]
        # 创建BM25模型实例
        self.bm25 = BM25Okapi(tokenized_contents)

    def save(self, path):
        with open(path, 'w', encoding='utf8') as f:
            for i in self.code_list:
                f.write(json.dumps(i))
                f.write('\n')

    def rerank_bm25(self, doc):
        # 对文章和每个文档的内容进行分词
        tokenized_doc = list(jieba.cut(doc))

        # 计算每个文档的BM25得分
        doc_scores = self.bm25.get_scores(tokenized_doc)

        # 将得分与标题结合，准备排序
        scored_docs = [{"score": score, "query": query} for score, query in
                       zip(doc_scores, self.query_list)]

        # 根据得分进行排序，得分最高的在前
        scored_docs.sort(reverse=True, key=lambda x: x['score'])
        return scored_docs

    def recall_code_by_score(self, doc, score=10):

        scored_docs = self.rerank_bm25(doc)
        return [self.code_dic[i['query']] for i in scored_docs if i['score'] > score]

    def recall_code_by_num(self, doc, num=5):
        scored_docs = self.rerank_bm25(doc)
        return [self.code_dic[i['query']] for i in scored_docs[:num]]

    def recall_code_by_token(self, doc, token=2000):
        # self.code_dic = {i['function_doc']:i for i in self.code_list}
        n_token = 0
        scored_docs = self.rerank_bm25(doc)
        functions = []
        for i in scored_docs:
            n_token += len(i['code'])
            if n_token > token:
                break
            functions.append(self.code_dic[i['query']])
        print(f'召回{len(functions)}条函数')
        return functions

    # def recall_code_by_rule(self, doc):
    #
    #     from
    #     for i in
    #
    #     # self.code_dic = {i['function_doc']:i for i in self.code_list}
    #     n_token = 0
    #
    #     scored_docs = self.rerank_bm25(doc)
    #     functions = []
    #     for i in scored_docs:
    #         print(i['score'])
    #         n_token+=len(i['query'])
    #         if n_token>token:
    #             break
    #         functions.append(i['query'])
    #     print(f'召回{len(functions)}条函数')
    #     return functions


class RecallQuestion:
    def __init__(self, path):
        self.qc = []
        with open(path, encoding='utf8') as f:
            for line in f:
                self.qc.append(json.loads(line))

    def get_plan(self, question):
        # 计算每个问题与给定问题的相似度分数
        question = question.split('\n')[0]
        for item in self.qc:
            item['score'] = fuzz.ratio(item['question'], question)

        # 按照得分排序
        sorted_items = sorted(self.qc, key=lambda x: x['score'], reverse=True)

        for i in sorted_items:
            if question[:5] not in i['question']:  # 确保不会召回原题以及改编题
                # second_highest_scored_item = sorted_items[5]
                res = f"问题：{i['question']}\n回答：{i['plan']}"
                inx = res.rfind('```') + 3
                return res[:inx]
