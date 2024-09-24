from agents.agents import SearchPlannerAgent, ResultSelectorAgent, EndNodeAgent
from langgraph.graph import StateGraph
from prompts.prompts import search_planner_prompt_template, result_selector_prompt_template
from states.state import AgentGraphState, get_agent_graph_state
from tools.google_serper import get_google_serper
from tools.website_scraper import scrape_website
from utils.helper_functions import log_function_call
from models_config import models
from typing import Dict, Union

@log_function_call
def create_graph(models: Dict[str, Dict[str, Union[str, None]]], stop=None, model_endpoint=None, temperature=0):
    """
        Creates the workflow of LLM agents.

    Args:
        models (Dict[str, Dict[str, Union[str, None]]]): A list of LLMs models that can be used be the workflow.
        stop (str, optional): Condition (word/character) that decides when the agent should stop generating a response.
        model_endpoint (str, optional): Local model endpoint if not using cloud agent.
        temperature (float, optional): Model temperature i.e. level of model creativity.

    Returns:
        StateGraph: A graph representing the workflow of LLM agents.
    """
    # Creates a graph that represents a workflow of agents. The objective of the workflow is to generate a response to the user query.
    graph = StateGraph(AgentGraphState)

    ############################# Set and execute search planner node ####################################
    # Add the search planner node. This node uses the SearchPlannerAgent to generate a search plan (state)
    # based on the research question and feedback from the reviewer. The first parameter is the name
    # of the node. The second parameter is a call to a function that returns a state.

    def search_planner_agent(state): 
        return SearchPlannerAgent(state=state, 
                                   model=models.models["openai"]["model"], 
                                   server=models.models["openai"]["server"], 
                                   temperature=temperature, stop=stop)
    
    def get_search_planner_invoke(state):
        return search_planner_agent(state).invoke(
            research_question=state["research_question"], 
            feedback=lambda: get_agent_graph_state(state=state, state_key="reviewer_response"), 
            prompt=search_planner_prompt_template
        )

    graph.add_node("search_planner", get_search_planner_invoke)

    ############################# Set and execute search tool node ####################################
    # Add the web search tool node. This node performs a web search, based on instructions from the planner node (previous node).
    # Uses the Google Serper tool and only uses the last response from the planner.
    graph.add_node("web_search_tool",
        lambda state: get_google_serper(state=state, 
                                        get_plan=lambda: get_agent_graph_state(state=state, 
                                                                               state_key="search_planner_response", 
                                                                               retrieve_all=False)))

    ############################# Set and execute result selector node ####################################
    # Add the result selector agent node. This node selects relevant search results based on the
    # research question, feedback from the reviewer, and the results from the web search.
    def result_selector_agent(state):
        return ResultSelectorAgent(state, 
                                   model=models.models["openai"]["model"], 
                                   server=models.models["openai"]["server"], 
                                   temperature=temperature, 
                                   stop=stop)
    
    def result_selector_agent_invoke(state):
        return result_selector_agent.invoke(research_question=state["research_question"], 
                                                            feedback=lambda: get_agent_graph_state(state=state, 
                                                                                                 state_key="reviewer_response", 
                                                                                                 retrieve_all=True), 
                                                            web_search_result=lambda: get_agent_graph_state(state=state, 
                                                                                                            state_key="web_search_response", 
                                                                                                            retrieve_all=False),

                                                            previous_selections=lambda: get_agent_graph_state(state=state, 
                                                                                                              state_key="result_selector_response", 
                                                                                                              retrieve_all=True),
                
                                                            prompt=result_selector_prompt_template)
    

    graph.add_node("result_selector_agent", result_selector_agent_invoke)

    ############################# Set and execute scraper tool node ####################################
    # Add the scraper tool node. This node scrapes the selected website that was chosen by the result selector node.
    graph.add_node("scraper_tool", lambda state: scrape_website(state=state, 
                                                                selected_website=lambda: get_agent_graph_state(
                                                                state=state, 
                                                                state_key="result_selector_response", 
                                                                retrieve_all=True)))

    # Add the reviewer node. This node reviews the scraped data and decides whether it answers the user's query.
    # graph.add_node("reviewer", lambda graph_state: ReviewerAgent(
    #     state, model, server, temperature, model_endpoint, stop).invoke(state["research_question"]))

    # Add the presenter node. This node presents the node to the  - undecided what will actually be done with this node.
    # graph.add_node("presenter", lambda graph_state: PresenterAgent(
    #     state, model, server, temperature, model_endpoint, stop).invoke(state["research_question"]))

    graph.add_node("end", lambda state: EndNodeAgent(state).invoke())

    # Define graph edges
    graph.set_entry_point("search_planner")
    graph.add_edge("search_planner", "web_search_tool")
    graph.add_edge("web_search_tool", "result_selector_agent")
    graph.add_edge("result_selector_agent", "scraper_tool")
    graph.add_edge("scraper_tool", "end")

    return graph

@log_function_call
def compile_graph(graph):
    """
    Compiles the state graph into a `CompiledGraph` object.

    Args:
        graph (StateGraph): A class that defines the state of the agents.

    Returns:
        "CompiledStateGraph": 
    """
    workflow = graph.compile()
    return workflow