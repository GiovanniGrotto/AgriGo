from huggingface_hub import InferenceClient
import json
import os

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
        question = "What should I do if a plant is rusty"

    prompt = f"You are an assistant gardener, explain quickly and be concise on your answer. The question to answer is: {question}"
    response = llm_client.post(
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 200},
            "task": "text-generation",
        },
    )
    data = json.loads(response.decode())[0]["generated_text"]
    return data.split(prompt)[1]
