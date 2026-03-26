import os
from openai import OpenAI
import sys

# Try multiple endpoints
endpoints = [
    "https://generativelanguage.googleapis.com/v1beta/openai/",
    "https://generativelanguage.googleapis.com/v1/openai/",
]

api_key = "AIzaSyD4YKKSJ7robWbM6iaexZ4as09MyISqx-c"

for base_url in endpoints:
    print("Testing endpoint: " + base_url)
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        models = client.models.list()
        print("Available models:")
        for model in models:
            print("- " + str(model.id))
    except Exception as e:
        print("Error with " + base_url + ": " + str(e))
    print("-" * 20)
