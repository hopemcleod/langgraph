from langchain_openai import ChatOpenAI
from utils.helper_functions import log_function_call

class LLM_Model():
    @log_function_call
    def __init__(self, model, server, temperature):
        self.model = model
        self.server = server
        self.temperature = temperature
    
class OpenAI_LLM(LLM_Model):
    DEFAULT_MODEL = 'gpt-3.5-turbo'
    DEFAULT_SERVER = 'openai'
    DEFAULT_TEMPERATURE = 0

    @log_function_call
    def __init__(self, model=DEFAULT_MODEL, server=DEFAULT_SERVER, temperature=DEFAULT_TEMPERATURE):
        super().__init__(model, server, temperature)
    
    @log_function_call
    def get_openai(self):
        llm = ChatOpenAI(model=self.model, temperature=self.temperature)
        return llm

    @log_function_call
    def get_openai_json(self):
        llm = ChatOpenAI(model=self.model, temperature=self.temperature, model_kwargs={
                        "response_format": {"type": "json_object"}})
        return llm
    
class Llama_LLM(LLM_Model):
    DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    DEFAULT_SERVER = None
    DEFAULT_TEMPERATURE = 0


    # def __init__(self, temperature=0, model="Meta-Llama-3-8B-Instruct-imatrix"):
    # def __init__(self, temperature=0, model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF"):
    def __init__(self, model="meta-llama/Meta-Llama-3.1-8B-Instruct", server=DEFAULT_SERVER, temperature=0):
        super().__init__(model, server, temperature)
        # self.headers = {"Content-Type": "application/json"}
        self.local_model_endpoint = "http://localhost:1234/v1/chat/completions"
        self.temperature = temperature
        self.model = model

# apply_decorator_to_all_functions(sys.modules[__name__], print_function_name)