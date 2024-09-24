from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from utils.helper_functions import log_function_call
import sys

class AgentGraphState(TypedDict):
    """
        Represents the state of an agent-driven workflow in a graph-based system.

        This state is used to track responses between various agents involved in the graph.

        Attributes:
            research_question (str): The main research question or query driving the workflow.
            search_planner_response (list): A list of responses returned from the search planner agent.
            web_search_response (list): A list of formatted data (consisting of title, link, snippet) returned by the web search tool.
            result_selector_response (list): A list of responses returned from the result selector agent.
            scraper_response (list): A list of formatted data (url source, content) returned by the web scraper agent.
            reviewer_response (list): A list of responses returned by the reviewer agent.
            presenter_response (list): A list of messages from the presenter agent, likely preparing final output.
    """    
    research_question: str
    search_planner_response: Annotated[list, add_messages]
    web_search_response: Annotated[list, add_messages]
    result_selector_response: Annotated[list, add_messages] # In the futre, might select more than on result and create a CV for them both
    scraper_response: Annotated[list, add_messages]
    reviewer_response: Annotated[list, add_messages]
    presenter_response: Annotated[list, add_messages]
    writer_response: Annotated[list, add_messages]

state = {
    "research_question": "",
    "search_planner_response": [],
    "web_search_response": [],
    "result_selector_response": [],
    "scraper_response": [],
    "reviewer_response": [],
    "presenter_response": [],
    "writer_response": [],
}

@log_function_call
def get_agent_graph_state(state:AgentGraphState, state_key: str, retrieve_all: bool = True):
    """
        Gets either all of the state or just the latest response. 
        If retrieve_all is false, assume that the last response only
        should be retrieved.

        Args:
            state (AgentGraphState): _description_
            state_key (str): _description_
            retrieve_all (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
    """
    if state_key in state:
       return state[state_key] if retrieve_all else state[state_key][-1]






