from agent_graph.graph import create_graph, compile_graph
from models_config import models
from models.models import Llama_LLM, OpenAI_LLM
from termcolor import colored

def generate_graph_workflow():
    """
    Generates a agentic graph workflow.

    Returns:
        CompiledStateGraph
    """
    # Create an agent workflow 
    graph = create_graph(models)

    # Compile the graph
    return compile_graph(graph)

if __name__ == "__main__":
    """
        Calls each agent in the agent workflow and outputs responses as they are returned.
        The iterations specifies the number of complete cycles of the workflow. The
        output is streamed to the console using colour to help differentiate between the
        different agents.

        TODO: Not clear. This workflow will have a reviewer step and so does that mean
        that an iteration could go on endlessly?
    """
    workflow = generate_graph_workflow()

    # For development purposes only. The  user input will be taken from a UI field.
    questions = ["Provide a summary of what the best exercises are for low back pain. Take these summaries from at least 5 evidence based papers."]
    user_question: str = questions[0]    
    iterations = 10

    while True:
        if user_question.lower() == "exit":
            break

        initial_input = {"research_question": user_question}

        # The stream method is particularly useful for long-running processes
        # or workflows where you want to see intermediate results without waiting
        #  for the entire process to complete. See https://python.langchain.com/v0.2/docs/how_to/streaming/
        # and https://python.langchain.com/v0.2/docs/concepts/
        for event in workflow.stream(initial_input, {"recursion_limit": iterations}):
            print(colored(f"\nState Dictionary: {event}\n", "green"))
        
