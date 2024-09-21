from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from utils.helper_functions import log_function_call
import sys

class AgentGraphState(TypedDict):
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

'''
Gets either all of the state or just the latest response. 
If retrieve_all is false, assume that the last response only
should be retrieved.
'''
@log_function_call
def get_agent_graph_state(state:AgentGraphState, state_key: str, retrieve_all: bool = True):
    if state_key in state:
       return state[state_key] if retrieve_all else state[state_key][-1]






