import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)



messages = [
    {
        "role": "system",
        "content": "You are Michael, a friendly AI assistant created by Neeal. Keep the ans short and concise."
    }
]

def ask_ai(user):
    global messages

    messages.append({
        "role": "user",
        "content": user
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )

    reply = response.choices[0].message.content

    messages.append({
        "role": "assistant",
        "content": reply
    })

    return reply

def ask_once(prompt):
    respone = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"user",
                "content": prompt
            }
        ]
    )
    return respone.choices[0].message.content