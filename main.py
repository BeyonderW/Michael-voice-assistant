import re
from ai import ask_ai
from listen import listen
from speak import speak
from dispatcher import dispatch
from router import classify_request
from web_search import web_search
import asyncio

mode = input("Choose mode (t=typing, s=speaking): ").strip().lower()

while True:
    try:
        if mode == "t":
            user = input("You: ")
        else:
            user = listen()

        if not user:
            continue

        if any(word in user.lower() for word in [
            "exit", "bye", "goodbye", "good bye", "see you", "quit", "stop"
        ]):
            asyncio.run(speak("Goodbye sir!", allow_interrupt=False))
            break

        request = classify_request(user)

        intent = request["intent"]
        entity = request["entity"]

        print("Intent :", intent)
        print("Entity :", entity)

        # Temporary until commands.py is refactored
        command = dispatch(intent, entity)

        if command:
            reply = command

        elif intent == "WEB":

            results = web_search(user)

            if results:

                context = ""

                for result in results[:5]:
                    context += (
                        f"Title: {result['title']}\n"
                        f"Snippet: {result['body']}\n\n"
                    )

                prompt = f"""
You are Michael, a friendly AI assistant created by Neeal.

Answer in 2-3 short spoken sentences, like you're talking out loud - not writing a report.

Do NOT use markdown, bullet points, bold text, or headers. Plain spoken sentences only.

Use the search results below to answer.

If the user asks for latest news, pick the single most relevant/interesting story and summarize just that in 1-2 sentences.

Do NOT tell the user to check Google, CNN or Reuters.

User:
{user}

Search Results:
{context}
"""

                reply = ask_ai(prompt)

            else:
                reply = "I couldn't find anything."

        else:
            reply = ask_ai(user)

        print("Michael:", reply)

        # Strip markdown formatting that shouldn't be spoken aloud
        reply = re.sub(r"\*\*(.*?)\*\*", r"\1", reply)
        reply = re.sub(r"\*(.*?)\*", r"\1", reply)
        reply = (
            reply.replace("* ", "")
                 .replace("• ", "")
                 .replace("#", "")
        )

        asyncio.run(speak(reply, allow_interrupt=(mode == "s")))

    except Exception as e:
        print("Error:", e)