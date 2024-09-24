# https://api.python.langchain.com/en/v0.1/community_api_reference.html#module-langchain_community.llms
models = {
    "openai": {"server": None, "model": "gpt-4o"},
    "ollama": {"server": None, "model":"llama2"},
    "local_llama": {"server": "http://localhost:1234/v1/chat/completions", "model":"meta-llama/Meta-Llama-3.1-8B-Instruct"} # Selected in LM Studio
} 