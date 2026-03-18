from django.test import TestCase

# Create your tests here.
from gpt4all import GPT4All

print("Loading LLaMA 3.2 3B Instruct model...")
llm = GPT4All("Llama-3.2-3B-Instruct-Q4_0.gguf", model_path="C:/Users/tarun/AppData/Local/nomic.ai/GPT4All")

with llm.chat_session():
    response = llm.generate("Explain what Python decorators are in simple terms.", max_tokens=200)
    print("\n--- Model Response ---\n")
    print(response)
