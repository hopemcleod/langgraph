import json
from typing import Any, Callable, Union
from langchain_community.utilities import GoogleSerperAPIWrapper
import os
from termcolor import colored 
import requests
from states.state import AgentGraphState
from utils.helper_functions import load_config, log_function_call, validate_json

config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

@log_function_call
def format_results(organic_results):
    temp_links = []
    result_strings = []
    for result in organic_results:
        # The keys returned in the organic section of a call to the Google Serper API can vary. But common ones are returned and
        # 3 of them are referred to in this function
        title = result.get("title", "No title") # The title of the webpage
        link = result.get("link", '#' ) # The link of the webpage
        temp_links.append(link)
        snippet = result.get("snippet", "No snippet available") # A brief description or snippet of the content of the webpage
        result_strings.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n---")
    

    # Open file in write mode -  writing to a file is for debug only
    with open("result_links.txt", "w") as file:
        file.writelines(item + "\n" for item in temp_links)  # Add newlines manually

    return '\n'.join(result_strings)

# SERPer (Search Engine Results Page)
@log_function_call
def get_google_serper(state: AgentGraphState, get_plan: Callable[[], Any]):
    # Load config - contains API keys e.g. OpenAI and Google Serper servers
    load_config(config_path)

    # Get the search_planner_agent's plan
    plan_data = get_plan().content # The state is storing a list of OpenAI HumanMessage objects that has a property called 'content'
    print(colored(plan_data, "magenta"))
    try:
        plan_data = json.loads(plan_data)
        search = plan_data.get("search_term")

        print(colored(f"The following is going to be used for the serper search: {search}\n", "blue"))
        web_searcher_server_url = "https://google.serper.dev/search"
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': os.environ['SERPER_API_KEY']
        }

        payload = json.dumps({'q': search})

        # Ready to make a POST request to Google Serper
        response = requests.post(web_searcher_server_url, headers=headers, data=payload)
        response.raise_for_status() # Raise an HTTPError for bad responses (4XX, 5XX)
        results = response.json()

        # Check if 'organic' key is in the results (NB: 'organic' is a key in a dictionary, specifically representing 
        # the organic (natural, non-paid) search results returned by the Google Serper API.)
        if 'organic' in results:
            formatted_results = format_results(results['organic'])

            ## Note that when objects, classes, dictionaries, or lists are passed in to a function,
            # it is the ref that is beig passed in. It can therefore be modified directly.
            print(colored(f"Web search results:{formatted_results}\n", 'light_blue'))
            return {**state, 'web_search_response': formatted_results}
        else:
            return {**state, 'web_search_response': 'No organic results found.'}
    except json.JSONDecodeError as e:
        validate_json(plan_data)
    
# copy of j. adeojo example
def x_get_google_serper(state:AgentGraphState, get_plan):
    load_config(config_path)

    plan_data = get_plan().content
    plan_data = json.loads(plan_data)
    search = plan_data.get("search_term")

    search_url = "https://google.serper.dev/search"
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': os.environ['SERPER_API_KEY']  # Ensure this environment variable is set with your API key
    }
    payload = json.dumps({"q": search})
    
    # Attempt to make the HTTP POST request
    try:
        response = requests.post(search_url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4XX, 5XX)
        results = response.json()
        
        # Check if 'organic' results are in the response
        if 'organic' in results:
            formatted_results = format_results(results['organic'])
            print(colored(f"Serper results:{formatted_results}\n", 'light_blue'))
            state = {**state, "web_search_response": formatted_results}
            return state
        else:
            return {**state, "web_search_response": "No organic results found."}
        


    except requests.exceptions.HTTPError as http_err:
        return {**state, "web_search_response": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {**state, "web_search_response": f"Request error occurred: {req_err}"}
    except KeyError as key_err:
        return {**state, "web_search_response": f"Key error occurred: {key_err}"}
