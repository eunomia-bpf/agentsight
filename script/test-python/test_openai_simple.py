#!/usr/bin/env python3
"""
Simple test program to generate OpenAI API traffic for testing decompression.
"""
import os
import sys

# Check if we have the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    print("Please export it: export OPENAI_API_KEY=your_key_here")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed")
    print("Please install it: pip install openai")
    sys.exit(1)

model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=api_key)

print(f"Sending request to OpenAI API (model: {model})...")
print("This traffic should be captured by sslsniff\n")

try:
    # Make a simple API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "Say hello in exactly 5 words"}
        ],
        max_completion_tokens=500
    )

    print("Response received:")
    print(response.choices[0].message.content)
    print("\nRequest completed successfully!")

except Exception as e:
    print(f"Error making API request: {e}")
    sys.exit(1)
