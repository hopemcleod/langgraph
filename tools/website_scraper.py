from bs4 import BeautifulSoup
import json
from langchain_core.messages import HumanMessage
import requests
from states.state import AgentGraphState

def is_garbled(text):
    # A simple heuristic to detect garbled text: high proportion of non-ASCII characters
    # NOTE to myself: The following is an example of a generator expression
    non_ascii_count = sum(1 for char in text if ord(char) > 127)
    return non_ascii_count > len(text) * 0.3

'''
selected_website is a function reference that when called gets the latest state
of the result_selector.
'''
def scrape_website(state: AgentGraphState, selected_website):
    # Call the selected_website function. The argument given is the address of a function that will get the most recent response
    website_info = selected_website() if callable(selected_website) else selected_website

    # from the result selector agent. Get the content from this HumanMessage.
    research_data = website_info[0].content
    
    # Convert the result_selector HumanMessage string into a JSON object
    website_content = json.loads(research_data)

    # Once it is a JSON object, get the chosen website URL (include error checking for if the URL key does not exist)
    try:
        url = website_content["selected_page_url"]
    except KeyError as e:
        # I think a new key is being created here called "error" - maybe not ideal calling is 'url' when an error but it makes the code more tidy
        # because need to return the 'url' in the HumanMessage at the end.
        url = website_content["error"]

    # Try getting the website page details (check the status tof the request)
    content = ''
    try:
        base_error_msg = "Error in scraping website."

        # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'}

        session = requests.Session()
        response = session.get(url, headers=headers)
        # response = requests.get('https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9529058/', headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the text content
        text = soup.stripped_strings

        # The example program adds a space - but not sure why yet
        content = ' '.join(text)

        # Check for garbled text
        if is_garbled(content):
            content = f"{base_error_msg}. Garbled text returned."
        else:
            # Might change the length of this.
            content = content[:8000]

    except requests.HTTPError as e:
        if e.response.status.code == 403:
            content = f"{base_error_msg} Permission denied (403) for URL: {url}"
        else:
            content = f"{base_error_msg}"
    
    except requests.RequestException as e:
        content = f"{base_error_msg}, {str(e)}"
    except Exception as e:
        pass
    finally:
        # could maybe use json.dumps instead of str. I think I would need to surrond {"source": url, "content": content} with double quotes though and therefore
        # would be "{'source': url, 'content': content}"
        state["scraper_response"].append(HumanMessage(
            role="system", content=str({"source": url, "content": content})))
        return {"scraper_response": state["scraper_response"]}

# Explanation of soup.stripped_strings:
    '''
     - stripped strings returns a generator ('texts' is a generator object and not a list). But it can be converted to a
        # list with list(soup.stripped_strings)
    HTML Tag Removal: Yes, stripped_strings effectively removes HTML tags, but not directly. It's a byproduct of how BeautifulSoup works.
    What stripped_strings actually does:

    It traverses the parsed document tree.
    It extracts only the text content from text nodes.
    It ignores the tags themselves.
    It strips whitespace from the beginning and end of each text segment.
    It skips any strings that consist entirely of whitespace.


    So, while it's not explicitly "stripping" HTML tags, the end result is that you get text content without HTML tags.
'''
