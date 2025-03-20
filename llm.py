import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from huggingface_hub import InferenceClient
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Replace this with your Hugging Face access token
access_token = os.getenv("ACCESS_TOKEN")
repo_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def call_llm(question: str):
    # Pass the access token to the InferenceClient
    llm_client = InferenceClient(
        model=repo_id,
        timeout=120,
        token=access_token  # Add the token here
    )
    if not question:
        question = "How can I handle the hot soil problem?"

    prompt = f"We are talking about agriculture. Answer to this question in ONLY ONE LINE: {question}"
    response = llm_client.post(
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 200},
            "task": "text-generation",
        },
    )
    data = json.loads(response.decode())[0]["generated_text"]
    return data.split(prompt)[1]
