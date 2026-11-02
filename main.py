import re
import sys
import asyncio
import threading
from ai import ask_ai
from listen import listen
from speak import speak
from dispatcher import dispatch
from router import classify_request
from web_search import web_search
from router import route_input , is_multistep_task

HOTKEY = "ctrl+shift+m"       # wake Michael
QUIT_HOTKEY = "ctrl+shift+q"  # shut Michael down (needed when running without a console)

FAREWELL = re.compile(r"\b(goodbye|good bye|bye|see you)\b")
BARE_EXIT_WORDS = {"exit", "quit", "stop", "exit michael", "quit michael", "stop michael"}


def is_exit(user):
    """
    True for 'goodbye', 'bye', 'see you', or a bare 'exit'/'quit'/'stop'.
    A bare-word match means 'quit spotify' or 'exit chrome' are NOT treated
    as 'shut down Michael' - they go to the router as app commands.
    """
    text = user.lower().strip(" .!?")
    return text in BARE_EXIT_WORDS or bool(FAREWELL.search(text))


def clean_for_speech(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return (
        text.replace("* ", "")
            .replace("• ", "")
            .replace("`", "")
            .replace("#", "")
    )


def process_request(user):
    """Runs one request through router -> dispatcher / web / AI. Returns reply text."""
    if is_multistep_task(user):
        return route_input(
            user_input=user,
            speak_callback=print, 
            status_callback=print
        )
    request = classify_request(user)

    intent = request["intent"]
    entity = request["entity"]

    print("Intent :", intent)
    print("Entity :", entity)

    command = dispatch(intent, entity)

    if command:
        return command

    if intent == "WEB":
        results = web_search(user)

        # web_search returns a plain string when nothing is found,
        # so only treat a real list of results as usable
        if isinstance(results, list) and results:
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
            return ask_ai(prompt)

        return "I couldn't find anything."

    return ask_ai(user)


def respond(reply, interruptible):
    print("Michael:", reply)
    asyncio.run(speak(clean_for_speech(reply), allow_interrupt=interruptible))


# ---------------------------------------------------------------
# Mode 1 and 2: typing (t) / always-listening (s) - same as before
# ---------------------------------------------------------------
def run_continuous(mode):
    while True:
        try:
            user = input("You: ") if mode == "t" else listen()

            if not user:
                continue

            if is_exit(user):
                asyncio.run(speak("Goodbye sir!", allow_interrupt=False))
                break

            reply = process_request(user)
            respond(reply, interruptible=(mode == "s"))

        except Exception as e:
            print("Error:", e)


# ---------------------------------------------------------------
# Mode 3: hotkey standby (h) - sits in the background until woken
# ---------------------------------------------------------------
def run_session():
    """One activation: listen, answer, keep listening for follow-ups until silence."""
    user = listen(timeout=8)

    while user:
        if is_exit(user):
            respond("Going on standby.", interruptible=False)
            return

        reply = process_request(user)
        respond(reply, interruptible=True)

        user = listen(timeout=6)  # follow-up window; silence ends the session


def run_hotkey_mode():
    import keyboard      # lazy import so typing/speaking modes work without it
    import winsound

    activate = threading.Event()
    quit_flag = threading.Event()

    # suppress=True stops the keypress reaching the app in front
    # (Ctrl+Shift+M is a shortcut in VS Code and Chrome)
    keyboard.add_hotkey(HOTKEY, activate.set, suppress=True)
    keyboard.add_hotkey(QUIT_HOTKEY, quit_flag.set, suppress=True)

    print(f"Michael on standby. {HOTKEY.upper()} = talk, {QUIT_HOTKEY.upper()} = quit.")

    while not quit_flag.is_set():
        if not activate.wait(timeout=0.5):
            continue

        activate.clear()
        winsound.Beep(900, 120)  # "I'm listening"

        try:
            run_session()
        except Exception as e:
            print("Error:", e)
        finally:
            activate.clear()     # drop any presses made while busy
            winsound.Beep(500, 120)  # back to standby

    keyboard.unhook_all()
    print("Michael shut down.")


if __name__ == "__main__":
    if "--background" in sys.argv:
        mode = "h"
    else:
        mode = input("Choose mode (t=typing, s=speaking, h=hotkey standby): ").strip().lower()

    if mode == "h":
        run_hotkey_mode()
    else:
        run_continuous(mode)