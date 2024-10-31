import time 
from llm.glm_llm import glm, client
import logging
import logging
import time
from utils import *


class ChainWrapper:
    """
    A wrapper for a LLM chain
    """

    def __init__(self, prompt_path: str, parser_func=None):
        
        """
        Initialize a new instance of the ChainWrapper class.
        :param llm_config: The config for the LLM
        :param prompt_path: A path to the prompt file (text file)
        :param parser_func: A function to parse the output of the LLM
        """
        self.llm = glm 
        self.parser_func = parser_func
        self.prompt = load_prompt(prompt_path)
        self.prompt_path =  prompt_path
        self.save_path = None
        self.build_chain()

    def build_chain(self):
        #    print("normal chaim")
           self.chain = self.prompt | self.llm 

    
    def set_save_folder(self, save_path):
         self.save_path = save_path
           
   
    def invoke(self, chain_input: dict) -> dict:
        """
        Invoke the chain on a single input
        :param chain_input: The input for the chain
        :return: A dict with the defined json schema
        """
        count = 0
        while 1:
           try:

               result = self.chain.invoke(chain_input)
               # print(result.content)
               if self.parser_func is not None and self.save_path == None:
                  result = self.parser_func(result)
               elif self.parser_func is not None and self.save_path != None:
                  result = self.parser_func(result, self.save_path)
               self.save_path = None
               #    print(result)
               break 
           except Exception as e:
                if "</div>" not in str(e):
                  print("Here is a error\n" ,str(e))
                  count += 1
                  result = None
                  time.sleep(5)
                if count >= 5:
                  logging.error('Error in chain invoke: {}'.format(e.user_message))
                  result = None
                  break 
        return result