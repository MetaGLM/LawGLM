

import re 
from langchain_community.vectorstores import FAISS 
# from tools.all_tools import com_all_tools
from tools.tools_register import get_tools, register_tool
from services.all_tools_service_register import * 
from utils import *

com_all_tools = get_tools()

class RetrieverWrapper:
    
    def __init__(self, embedding_model, vector_path, log_path = None):
        self.embedding_model = embedding_model
        self.vector_path = vector_path
        self.log_path = log_path
        self.build_retriever()
        
        
    def build_retriever(self):
        
        self.retriever = FAISS.load_local(self.vector_path, self.embedding_model,allow_dangerous_deserialization=True)
        
        
    def invoke(self, query: str, num_k: int = 10):
        
        embedding_vector = self.embedding_model.embed_query(query)
        docs = self.retriever.similarity_search_by_vector(embedding_vector, k = num_k )
        docs_text = [doc.page_content for doc in docs]
        # print(docs_text)
        return "\n".join(docs_text)
    
    def invoke_for_tools(self, query: str, choosed_tool, num_k: int = 8):
        
        embedding_vector = self.embedding_model.embed_query(query)
        docs = self.retriever.similarity_search_by_vector(embedding_vector, k = num_k )
        
        num_tools = [1,2,4,9,27]
        for tool in choosed_tool:
            if tool not in num_tools:
                num_tools.append(tool)
                
        for doc in docs:
            doc_file = doc.metadata['source']
            number = re.findall(r'(\d+)', doc_file )[0]
            # print(doc)
            if int(number) not in num_tools:
                num_tools.append(int(number))
            
        # print(num_tools)
        print("总工具数量：",len(com_all_tools))
        num_tools = sorted(num_tools, reverse=True)
        print(num_tools)
        return [com_all_tools[number] for number in num_tools]