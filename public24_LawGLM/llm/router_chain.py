from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import time 
from llm.glm_llm import glm
import logging
import importlib
import re 
from pathlib import Path
from agents.battle_agent import BattleAgent
import logging
import time
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS 
# from tools.all_tools import com_all_tools
from tools.tools_register import get_tools, register_tool
from services.all_tools_service_register import * 
from utils import *
from llm.AgentWrapper import AgentWrapper
from llm.ChainWrapper import ChainWrapper
from llm.RetrieverWrapper import RetrieverWrapper
#from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from preprocess import *
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
def chinese_tokenizer(text):
    return jieba.lcut(text)


com_all_tools = get_tools()

    
class MetaChain:
    """
    A wrapper for the meta-prompts chain
    """
    
    def __init__(self, target_path, log_path=None):
        """
        Initialize a new instance of the MetaChain class. Loading all the meta-prompts
        :param config: An EasyDict configuration
        """
        self.prompt_folder = Path("./prompt")
        #不需要 init , step_samples
        # self.initial_chain = self.load_chain('initial')
        # self.step_samples = self.load_chain('step_samples')
        self.log_path = log_path
        self.target_path = target_path
        #self.auto_tool_agent = None
        
       
        # self.is_omit_clf = self.load_chain('classification/is_omit_clf')
        
        
        self.embedding_model_path = "../models/text2vec-large-chinese"
        
        self.keywords = self.load_chain('preprocess/keywords')
        self.matchCol = self.load_chain('preprocess/matchCol')
        self.clearnoise = self.load_chain('preprocess/clearnoise')
        self.correction = self.load_chain('preprocess/correction')
        self.plan_shots_chain = self.load_chain('battle/plan_few_shot')
        self.plan_edit_shots_chain = self.load_chain('battle/plan_edit_few_shot')

        self.judge_chain = self.load_chain('battle/judge')

        self.regulator= self.load_chain("battle/regulator")
        
        
        self.summary_chain = self.load_chain("summary/summary")

        self.coder_shots = self.load_chain('coder/coder_few_shot') 
        self.coder_edit_shots= self.load_chain("coder/coder_edit_few_shot")

        self.few_shot_path = "./docs/few-shot/"
        self.all_embeddings = None
        print("load  Embedding model")


        # 创建TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(tokenizer=chinese_tokenizer)

        

        print("load Few shot")
        self.plans_list, self.coders_list, self.plans_embedding, self.coders_embedding, self.all_embeddings = self.load_few_shot()
        print("load  done")
        for plan in self.plans_list:
            print(plan)
        for coder in self.coders_list:
            print(coder)
         
         
    def load_chain(self, chain_name: str) -> ChainWrapper:
        """
        Load a chain according to the chain name
        :param chain_name: The name of the chain
        """
        metadata = get_chain_metadata( self.prompt_folder / '{}.prompt'.format(chain_name))
        return ChainWrapper(self.prompt_folder  /  '{}.prompt'.format(chain_name),
                            metadata['parser_func'])
              
        
    def build_retriever(self):
        model_kwargs = {"device": "cuda"}
        encode_kwargs = {"normalize_embeddings": True}
        self.bgeEmbeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_path, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
        )
        self.apis_retriever = FAISS.load_local("./embeddings/apis", self.bgeEmbeddings,allow_dangerous_deserialization=True)
        self.shema_retriever = FAISS.load_local("./embeddings/schema", self.bgeEmbeddings,allow_dangerous_deserialization=True)
    
    
    def build_auto_agent(self):
        prompt_path = self.prompt_folder / 'local_tools/auto_tools.prompt'
        return  AgentWrapper(prompt_path, self.apis_retriever, self.plan_chain,self.inter_summary_chain, self.judge_chain, log_path=self.log_path)
    

    def load_few_shot(self):
        file_folder = self.few_shot_path
        plans_list = []
        coders_list = []
        plans_questions = []
        coders_questions = []
        for file_name in os.listdir(file_folder):
            if file_name.endswith(".txt"):
                file_path = os.path.join(file_folder, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    test_data = f.read()
                    test_data = test_data.split("\n")
                    plan_dict, coder_list = parse_shot_data(test_data)
                    plan_dict['file_name'] = file_name
                    plan_question = plan_dict["question"]
                    if plan_question not in plans_questions:
                        plans_questions.append(plan_question)
                        plans_list.append(plan_dict)
                    for coder_dict in coder_list:
                        coder_question = coder_dict["question"]
                        if coder_question not in coders_questions:
                            coders_questions.append(coder_question)
                            coders_list.append(coder_dict)
        
        # 提取所有的问题
        plans_questions = [example["question"] for example in plans_list]
        coders_questions = [example["question"] for example in coders_list]
        # 训练TF-IDF模型并转换文本
        #### 训练语料使用target_path 作为QUESTION_ANSWER的语料
        with open(self.target_path, "r", encoding="utf-8") as f:
            target_data = f.readlines()
        questions = []
        for line in target_data:
            json_data = json.loads(line)
            questions.append(json_data["question"])
        self.tfidf_vectorizer.fit(questions)
        
        plans_embeddings = self.tfidf_vectorizer.transform(plans_questions)
        coders_embeddings = self.tfidf_vectorizer.transform(coders_questions)
        print("Few-shot Begin Embedding")
        # 批量计算嵌入
        from scipy.sparse import vstack

        all_embeddings = vstack((plans_embeddings, coders_embeddings))

        print("Few-shot END Embedding")


        return plans_list, coders_list, plans_embeddings, coders_embeddings, all_embeddings
    

    def find_most_similar_plans(self, query, schema_list, k=3):
        question_embedding = self.tfidf_vectorizer.transform([query])
        query_similarities = cosine_similarity(question_embedding, self.plans_embedding)[0]
        # 计算相似度
        similarities = []
        for plan, emmbedings_simlarity in zip(self.plans_list, query_similarities):
            schema_similarity = calculate_similarity(schema_list, plan['schema_list'])
            similarities.append((schema_similarity, emmbedings_simlarity, plan))

        # 按照schema相似度和col相似度排序
        similarities.sort(key=lambda x: (x[1], x[0]), reverse=True)

        # 获取前k个最相似的plans
        most_similar_plans = [item[2] for item in similarities[:k]]

        return most_similar_plans
    


    def find_most_similar_coders(self, query, tool_list, k=3):
        question_embedding = self.tfidf_vectorizer.transform([query])
        query_similarities = cosine_similarity(question_embedding, self.coders_embedding)[0]

        # 计算相似度
        similarities = []
        for coder, emmbedings_simlarity in zip(self.coders_list, query_similarities):
            tool_similarity = calculate_similarity(tool_list, coder['tools'])
            similarities.append((tool_similarity, emmbedings_simlarity, coder))

        # 按照schema相似度和col相似度排序
        similarities.sort(key=lambda x: (x[1], x[0]), reverse=True)

        # 获取前k个最相似的plans
        most_similar_plans = [item[2] for item in similarities[:k]]

        return most_similar_plans
            




           
   
  
  

