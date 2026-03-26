import os
from openai import OpenAI

# Using the key from app.py
api_key = "AIzaSyD4YKKSJ7robWbM6iaexZ4as09MyISqx-c"
base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

client = OpenAI(api_key=api_key, base_url=base_url)

try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error: {e}")
