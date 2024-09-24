from langchain_core.messages import HumanMessage
from models.models import OpenAI_LLM
from prompts.prompts import reviewer_prompt_template, reporter_presenter_prompt_template, writer_prompt_template
import requests
from states.state import AgentGraphState
from termcolor import colored
from typing import Callable, Optional, Any, List
from utils.helper_functions import get_current_utc_datetime
from utils.helper_functions import log_function_call

class Agent():
    @log_function_call
    def __init__(self, state: AgentGraphState, model: str=None, server: str=None, temperature: float=0, stop: str=None):
        """
        The base class for other agents.

        Args:
            state (AgentGraphState): state of agents and tools that can be used by the agents.
            model (str): The LLM model used by the agent.
            server (str): The endpoint of the model's API
            temperature (float, optional): Model temperature i.e. level of model creativity.
            stop (str, optional): Condition (word/character) that decides when the agent should stop generating a response.
        """
        self.state = state
        self.model = model
        self.server = server
        self.temperature = temperature
        self.stop = stop

    @log_function_call
    def get_llm(self, json_model: bool =True):
        """
            Using the specified LLM model, return an LLM instance. Temporarily works with openai for now.

            Args:
                model (str): LLM model to get instance for.
                json_model (bool, optional): Indicates whether model response should be in JSON or not. Defaults to True.

            Returns:
                ChatOpenAI: Instance of the specified model.
        """
        openai_llm = OpenAI_LLM(temperature=self.temperature, model=self.model, server=self.server)
        return openai_llm.get_openai_json() if json_model else openai_llm.get_openai()
    
    @log_function_call
    def update_state(self, key: str, value: str | list[str | dict]):
        """
            Updates the state dictionary.

            Args:
                key (str): The key of the state dictionary to update/override.
                value (str | list[str  |  dict]): The key value to update/override.
        """
        self.state = {**self.state, key: value}

class SearchPlannerAgent(Agent):
    """
        Provides data and functions to help generate a web search plan.

    Args:
        Agent (class): Base class for all agents.
    """
    @log_function_call
    def invoke(self, research_question: str, prompt: str=None, feedback: Callable[[], Any]=None):
        """
            Calls the LLM with instructions/messages to help it make a web search plan.

            Args:
                research_question (str): User query.
                prompt (str): Prompt template for system message.
                feedback (Callable[[], Any]): Information from the Reviewer node. Defaults to None.

            Returns:
                AgentGraphState | dict[str, Any]: State updated with LLM response.
        """
        # get the current state of the reviewer agent
        feedback_value = feedback() if callable(feedback) else feedback #TODO - Should be a callable should modify this expression

        # format the the agent's prompt
        searcher_prompt = prompt.format(
            feedback=feedback_value, 
            datetime=get_current_utc_datetime)
        # setup the messages that are going to be sent to the LLM
        messages = [
            {"role": "system", "content": searcher_prompt},
            {"role": "user", "content": f"research_question: {research_question}"}
        ]

        if self.server is not None:
            # https://github.com/ollama/ollama/blob/main/docs/api.md
            payload = {"model": self.model, "format": "json", "stream": False, "temperature": 0, "messages": messages}
            try:
                # Send request to local LLM endpoint
                http_response = requests.post(
                    self.server,
                    headers={"Content-Type": "application/json"}, 
                    json=payload
                    )
                
                request_response_json = http_response.json()
                content: str = request_response_json['choices'][0]['message']['content']
                index = content.find('"search_term"')

                if index != -1:
                    if not content.endswith('}'):
                        content += '}'

                    response_formatted = HumanMessage(content=content)
                    self.state["search_planner_response"] = response_formatted
                    return self.state
                
                ############## local endpoint or not, set the state and return ##################    
                self.state["search_planner_response"] = content
                return self.state
                         
            except requests.exceptions.HTTPError as http_err:
                return {f"HTTP error occurred: {http_err}"}
            except requests.exceptions.RequestException as req_err:
                return {f"Request error occurred: {req_err}"}
            except KeyError as key_err:
                return {f"Key error occurred: {key_err}"}
        else:
            # get the LLM - as a temp measure only uses openai at the moment
            llm = self.get_llm(self.model)

            # call the LLM with the prompt and context
            llm_response = llm.invoke(messages)

            # get the response
            response = llm_response.content
            ############## local endpoint or not, set the state and return ##################    
            # update the state with the response
            self.state["search_planner_response"] = response
            return self.state   

class ResultSelectorAgent(Agent):
    """
        Provides data and functions to result selector agent choose a web result.
    Args:
        Agent (class): Base class for all agents.
    """
    @log_function_call
    def invoke(self, research_question: str, web_search_result: Callable[[], Any]=None, 
               prompt: str=None, previous_selections: Callable[[], List[Any]]=None, 
               feedback: Callable[[], Any]=None):
        """
            Calls the LLM with instructions/messages so that it can select the best web page result/URL.

            Args:
                research_question (str): User query.
                web_search_result (Callable[[], Any]): 
                previous_selections (Callable[[], List[Any]]):
                prompt (str): Prompt template for system message.
                feedback (Callable[[], Any]): Information from the Reviewer node. Defaults to None.

            Returns:
                AgentGraphState | dict[str, Any]: State updated with LLM response.
        """
        # Get the latest state of the reviewer
        reviewer_advice = feedback() if callable(feedback) else feedback
        web_results = web_search_result() if callable(web_search_result) else web_search_result
        selections = previous_selections() if callable(previous_selections) else previous_selections

        # Format this agent's prompt. Need: last result from web_search (Serper), 
        # reviewer last feedback, previous selector responses, date
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
        if self.server is not None:
            payload = {"model": self.model, "format": "json", "stream": False, "temperature": 0, "messages": messages}

            try:
                http_response = requests.post(
                    self.server, 
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
