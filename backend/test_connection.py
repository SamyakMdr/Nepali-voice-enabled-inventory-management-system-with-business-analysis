from ollama import chat

response = chat(
    model="mistral",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)

print(response['message']['content'])
