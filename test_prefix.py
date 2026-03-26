import os
from openai import OpenAI
import sys

# Using the key from app.py
api_key = "AIzaSyD4YKKSJ7robWbM6iaexZ4as09MyISqx-c"
base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

client = OpenAI(api_key=api_key, base_url=base_url)

# Try with no prefix
try:
    print("Testing gemini-2.5-flash (no prefix)...")
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("Success: " + response.choices[0].message.content)
except Exception as e:
    print("Error with gemini-2.5-flash: " + str(e))

# Try with models/ prefix
try:
    print("Testing models/gemini-2.5-flash (with prefix)...")
    response = client.chat.completions.create(
        model="models/gemini-2.5-flash",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("Success: " + response.choices[0].message.content)
except Exception as e:
    print("Error with models/gemini-2.5-flash: " + str(e))
