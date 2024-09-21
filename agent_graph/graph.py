from states.state import AgentGraphState, state, get_agent_graph_state
from langgraph.graph import StateGraph
from agents.agents import SearchPlannerAgent, ResultSelectorAgent, ReviewerAgent, PresenterAgent, WriterAgent, EndNodeAgent
from tools.google_serper import get_google_serper
from utils.helper_functions import log_function_call
import sys
from prompts.prompts import search_planner_prompt_template, result_selector_prompt_template
from termcolor import colored
from tools.website_scraper import scrape_website

# Define the graph workflow


@log_function_call
def create_graph(server=None, model=None, stop=None, model_endpoint=None, temperature=0):
    graph = StateGraph(AgentGraphState)

    # Define agent nodes - in the future the diffet agent nodes could use different models/servers if they wanted.
    # Passing these into the create_graph function assumes that all these agents are using the same model/server.
    graph.add_node(
        "search_planner",
        lambda state: SearchPlannerAgent(
            state=state,
            model=model,
            server=server,
            temperature=temperature,
            local_model_endpoint=model_endpoint,
            # local_model_endpoint=None,
            stop=stop).invoke(
                research_question=state["research_question"],

                feedback=lambda: get_agent_graph_state(
                    state=state, state_key="reviewer_response"),

                prompt=search_planner_prompt_template
        )
    )

    graph.add_node(
        "web_search_tool",
        lambda state: get_google_serper(
            state=state,
            get_plan=lambda: get_agent_graph_state(
                # Because retrieve_all is False, it will only retrieve the last message for the search_planner
                state=state, state_key="search_planner_response", retrieve_all=False)
        )
    )

    graph.add_node(
        "result_selector_agent",
        lambda state: ResultSelectorAgent(
            state,
            model,
            server,
            temperature,
            local_model_endpoint=model_endpoint,
            # local_model_endpoint=None,
            stop=stop).invoke(
                research_question=state["research_question"],

                feedback=lambda: get_agent_graph_state(
                    state=state, state_key="reviewer_response", retrieve_all=True),

                web_search_result=lambda: get_agent_graph_state(
                    state=state, state_key="web_search_response", retrieve_all=False),

                previous_selections=lambda: get_agent_graph_state(
                    state=state, state_key="result_selector_response", retrieve_all=True),
                
                prompt=result_selector_prompt_template))
    
    graph.add_node(
        "scraper_tool",
        lambda state: scrape_website(
            state=state,
            selected_website=lambda: get_agent_graph_state(
                # Because retrieve_all is False, it will only retrieve the last message for the search_planner
                state=state, state_key="result_selector_response", retrieve_all=True)
        )
    )

    # graph.add_node("reviewer", lambda graph_state: ReviewerAgent(
    #     state, model, server, temperature, model_endpoint, stop).invoke(state["research_question"]))

    # graph.add_node("presenter", lambda graph_state: PresenterAgent(
    #     state, model, server, temperature, model_endpoint, stop).invoke(state["research_question"]))

    # graph.add_node("writer", lambda graph_state: WriterAgent(
    #     state, model, server, temperature, model_endpoint, stop).invoke(state["research_question"]))

    graph.add_node("end", lambda state: EndNodeAgent(state).invoke())

    # Define graph edges
    graph.set_entry_point("search_planner")
    graph.add_edge("search_planner", "web_search_tool")
    graph.add_edge("web_search_tool", "result_selector_agent")
    graph.add_edge("result_selector_agent", "scraper_tool")
    graph.add_edge("scraper_tool", "end")

    # graph.set_finish_point("end")
    # graph.add_edge("searcher", "reviewer")
    # graph.add_edge("reviewer", "presenter")
    # graph.add_edge("presenter", "writer")
    # graph.add_edge("writer", "end")

    return graph


@log_function_call
def compile_graph(graph):
    workflow = graph.compile()
    return workflow

# apply_decorator_to_all_functions(sys.modules[__name__], print_function_name)
