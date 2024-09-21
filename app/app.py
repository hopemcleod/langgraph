# Imports
from agent_graph.graph import create_graph, compile_graph
from models.models import Llama_LLM, OpenAI_LLM
from utils.helper_functions import apply_decorator_to_all_functions, print_function_name
import sys
from termcolor import colored


model = OpenAI_LLM(model='gpt-4o')
# model = Llama_LLM(model="meta-llama/Meta-Llama-3.1-8B-Instruct")

# Define the agent graph
graph = create_graph(server=model.server, model=model.model)
# graph = create_graph(server=model.server, model=model.model, model_endpoint=model.local_model_endpoint)

# Compile the graph
workflow = compile_graph(graph)

# temp 
question: str = "Find me 5 evidence based articles on low back pain."

user_question = question

# Main function - use this to get input from the user
iterations = 10
if __name__ == "__main__":
    # apply_decorator_to_all_functions(sys.modules[__name__], print_function_name)

    while True:
        # user_question = input("How can I help?: ") # temp removal
        if user_question.lower() == "exit":
            break

        initial_input = {"research_question": user_question}

        # The stream method is particularly useful for long-running processes
        # or workflows where you want to see intermediate results without waiting
        #  for the entire process to complete. See https://python.langchain.com/v0.2/docs/how_to/streaming/
        # and https://python.langchain.com/v0.2/docs/concepts/
        for event in workflow.stream(initial_input, {"recursion_limit": iterations}):
            print(colored(f"\nState Dictionary: {event}\n", "green"))
        
