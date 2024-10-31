
from llm.glm_llm import glm
from agents.battle_agent import BattleAgent
from llm.ChainWrapper import ChainWrapper
from llm.RetrieverWrapper import RetrieverWrapper
from utils import *

class AgentWrapper:
    def __init__(self, prompt_path: str, tools_retriever: RetrieverWrapper,  planing_chain:ChainWrapper , inter_summary_chain:ChainWrapper ,judge_chain:ChainWrapper ,log_path = None, parser_func=None, ):
        
        """
        Initialize a new instance of the ChainWrapper class.
        :param llm_config: The config for the LLM
        :param prompt_path: A path to the prompt file (text file)
        :param parser_func: A function to parse the output of the LLM
        """
        self.llm = glm 
        
        self.parser_func = parser_func
        self.prompt = load_prompt(prompt_path, is_template=False)
        self.tools_retriever = tools_retriever
        self.log_path = log_path
        self.judge_chain = judge_chain
        self.planing_chain = planing_chain
        self.inter_summary_chain = inter_summary_chain
        self.build_agent()
        
        
    def build_agent(self):
        self.agent = BattleAgent(self.prompt, self.tools_retriever, self.planing_chain, self.inter_summary_chain, self.judge_chain,log_path=self.log_path)
            
            
    def invoke(self, query: str,judge_turn_num:int = 15, player_turn_num:int = 10):
        messages =  self.agent.invoke(query,judge_turn_num,player_turn_num )
        return  messages




