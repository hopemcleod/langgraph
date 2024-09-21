
import json
from langchain_core.messages import HumanMessage
from models.models import OpenAI_LLM
from prompts.prompts import reviewer_prompt_template, reporter_presenter_prompt_template, writer_prompt_template
import requests
from states.state import AgentGraphState
from termcolor import colored
from utils.helper_functions import get_current_utc_datetime
from utils.helper_functions import log_function_call

class Agent():
    @log_function_call
    def __init__(self, state: AgentGraphState, model=None, server=None, temperature=0, local_model_endpoint=None, stop=None):
        self.state = state
        self.model = model
        self.server = server
        self.temperature = temperature
        self.local_model_endpoint = local_model_endpoint
        self.stop = stop

    @log_function_call
    def get_llm(self, json_model=True):
        # Only going to specify one server/model
        openai_llm = OpenAI_LLM(temperature=self.temperature, model=self.model, server=self.server)
        return openai_llm.get_openai_json() if json_model else openai_llm.get_openai()
    
    @log_function_call
    def update_state(self, key, value):
        self.state = {**self.state, key: value}


# Each agent's callable/function (in this case invoke() but it can be called anything), must take in a state and return a state
# State is accessible as input already because the self.state is part of the agent's superclass i.e. state does not have to be
# passed in explicitly because invoke has implicit use of it from its Agent superclass.
# Web search agent
class SearchPlannerAgent(Agent):
    @log_function_call
    def invoke(self, research_question, prompt=None, feedback=None):
        # get the current state of the reviewer agent
        feedback_value = feedback() if callable(feedback) else feedback

        # format the the agent's prompt
        searcher_prompt = prompt.format(feedback=feedback_value, datetime=get_current_utc_datetime)

        # setup the messages that are going to be sent to the LLM
        messages = [
            {"role": "system", "content": searcher_prompt},
            {"role": "user", "content": f"research_question: {research_question}"}
        ]

        ############## Way model is called depends on if using a local model or not #####
        if self.local_model_endpoint is not None:
            payload = {
            "model": self.model,
            "format": "json",
            "stream": False,
            "temperature": 0,
            "messages": messages
            }

            try:
                http_response = requests.post(
                    self.local_model_endpoint, 
                    headers={"Content-Type": "application/json"}, 
                    json=payload
                    )
                
                request_response_json = http_response.json()
                content: str = request_response_json['choices'][0]['message']['content']
                # response = json.dumps(response)

                index = content.find('"search_term"')
                if index != -1:
                    if not content.endswith('}'):
                        content += '}'
                    response_formatted = HumanMessage(content=content)
                    self.state["search_planner_response"] = response_formatted
                    return self.state  
                ############## local endpoint or not, set the state and return ##################    
                # update the state with the response
                self.state["search_planner_response"] = content
                return self.state              
            except requests.exceptions.HTTPError as http_err:
                return {f"HTTP error occurred: {http_err}"}
            except requests.exceptions.RequestException as req_err:
                return {f"Request error occurred: {req_err}"}
            except KeyError as key_err:
                return {f"Key error occurred: {key_err}"}
        else:
            # get the LLM
            llm = self.get_llm()

            # call the LLM with the prompt and context
            llm_response = llm.invoke(messages)

            # get the response
            response = llm_response.content
            ############## local endpoint or not, set the state and return ##################    
            # update the state with the response
            self.state["search_planner_response"] = response
            return self.state   
            
        ############## local endpoint or not, set the state and return ##################    
        # update the state with the response
        # self.state["search_planner_response"] = response
        # return self.state
    
# Result selector agent

class ResultSelectorAgent(Agent):
    def invoke(self, research_question, previous_selections=None, web_search_result=None, prompt=None, feedback=None):
        # Get the latest state of the reviewer
        reviewer_advice = feedback() if callable(feedback) else feedback
        web_results = web_search_result() if callable(web_search_result) else web_search_result
        selections = previous_selections() if callable(previous_selections) else previous_selections

        # Format this agent's prompt. Need:
        # - last result from web_search (Serper)
        # - reviewer last feedback
        # - previous selector responses
        # - date

        result_selector_prompt = prompt.format(
            web_search_result=web_results, 
            feedback=reviewer_advice, 
            previous_selections=selections,
            datetime=get_current_utc_datetime()
            )

        # Setup the messgaes that are going to be sent to the LLM
        messages = [{'role': 'system', 'content': result_selector_prompt},
                    {'role': 'user', 'content': f'research_question: {research_question}'}]
        
        ############## Way model is called depends on if using a local model or not #####
        if self.local_model_endpoint is not None:
            payload = {
            "model": self.model,
            "format": "json",
            "stream": False,
            "temperature": 0,
            "messages": messages
            }

            try:
                http_response = requests.post(
                    self.local_model_endpoint, 
                    headers={"Content-Type": "application/json"}, 
                    json=payload
                    )
                
                request_response_json = http_response.json()
                content = request_response_json['choices'][0]['message']['content']

                # Update the state with the response
                self.update_state("result_selector_response", content)
                print(colored(f"result_selector_response: {content}", 'green'))               
            except requests.exceptions.HTTPError as http_err:
                return {f"HTTP error occurred: {http_err}"}
            except requests.exceptions.RequestException as req_err:
                return {f"Request error occurred: {req_err}"}
            except KeyError as key_err:
                return {f"Key error occurred: {key_err}"}
        else: 
            # Get the LLM instance
            llm = self.get_llm()

            # Call the LLM with prompt and context
            llm_response = llm.invoke(messages)

            # Get the content of the response
            content = llm_response.content

            # Update the state with the response
            self.update_state("result_selector_response", content)
            print(colored(f"result_selector_response: {content}", 'green'))

        return self.state    

# Results reviewer agent
class ReviewerAgent(Agent):
    @log_function_call
    def invoke(self, research_question, prompt=reviewer_prompt_template, feedback=None):
        return self.state

# Results presenter agent
class PresenterAgent(Agent):
    @log_function_call
    def invoke(self, research_question, prompt=reporter_presenter_prompt_template, feedback=None):
        return self.state

# CV Writer agent
class WriterAgent(Agent):
    @log_function_call
    def invoke(self, research_question, prompt=writer_prompt_template, feedback=None):
        return self.state
    
class EndNodeAgent(Agent):
    @log_function_call
    def invoke(self):
        pass

# apply_decorator_to_all_functions(sys.modules[__name__], print_function_name)

