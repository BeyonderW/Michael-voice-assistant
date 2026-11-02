"""router.py - Routing pipeline integrating the Task Execution Engine."""
import re
import spacy
from intent import *
from entities import extract_app, extract_file
from website import extract_website
from typing import Callable , Optional
from ai import get_groq_client
from agent.planner import TaskPlanner
from agent.engine import TaskExecutionEngine

planner = TaskPlanner(groq_client=get_groq_client())

nlp = spacy.load("en_core_web_sm")

NEGATIVE_WORDS = {
    "not",
    "don't",
    "dont",
    "do not",
    "never",
    "stop",
    "cancel"
}


def _has_negation(user):
    for word in NEGATIVE_WORDS:
        # \b = word boundary, so "not" won't match inside "notepad"
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, user):
            return True
    return False


def classify_request(user):

    user = user.lower()
    doc = nlp(user)

    negated = _has_negation(user)

    if negated:
        return {
            "intent": NO_ACTION,
            "entity": None,
            "confidence": 1.0,
            "negated": True
        }

    app = extract_app(user)
    print("Detected app: ", app)
    file = extract_file(user)

    # App commands
    if app:
        for token in doc:

            if token.lemma_ in ["open", "launch", "start", "run"]:
                return {
                    "intent": OPEN_APP,
                    "entity": app,
                    "confidence": 0.98,
                    "negated": False
                }

            if token.lemma_ in ["close", "quit", "exit", "terminate"]:
                return {
                    "intent": CLOSE_APP,
                    "entity": app,
                    "confidence": 0.98,
                    "negated": False
                }
                # Websites
    if any(t.lemma_ in ["open", "launch", "go", "visit", "browse", "start"] for t in doc):
        site_url = extract_website(user)
        if site_url:
            return {
                "intent": OPEN_WEBSITE,
                "entity": site_url,
                "confidence": 0.95,
                "negated": False
            }

    # Screenshot
    if "screenshot" in user:
        return {
            "intent": SCREENSHOT,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # Camera
    if any(word in user for word in ["camera", "webcam", "photo"]):
        return {
            "intent": CAMERA,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # Time
    if "time" in user:
        return {
            "intent": TIME,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # Date
    if "date" in user or "today" in user:
        return {
            "intent": DATE,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # Volume
    if "volume up" in user:
        return {
            "intent": VOLUME_UP,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "volume down" in user:
        return {
            "intent": VOLUME_DOWN,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "mute" in user and "unmute" not in user:
        return {
            "intent": MUTE,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "unmute" in user:
        return {
            "intent": UNMUTE,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # Brightness
    if "brightness up" in user:
        return {
            "intent": BRIGHTNESS_UP,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "brightness down" in user:
        return {
            "intent": BRIGHTNESS_DOWN,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "maximum brightness" in user:
        return {
            "intent": MAX_BRIGHTNESS,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if "minimum brightness" in user:
        return {
            "intent": MIN_BRIGHTNESS,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    # File
    if file:
        return {
            "intent": FIND_FILE,
            "entity": file,
            "confidence": 0.95,
            "negated": False
        }

    # CodeChef Contests
    if any(word in user for word in ["codechef", "contest", "competitive programming"]):
        return {
            "intent": CODECHEF,
            "entity": None,
            "confidence": 0.95,
            "negated": False
        }

    if any(word in user.lower() for word in ["diagnostics", "telemetry", "benchmark", "system status"]):
        return {
            "intent": "DIAGNOSTICS", 
            "entity": None, 
            "confidence": 0.95, 
            "negated": False
        }

    if any(word in user.lower() for word in ["weather", "temperature", "forecast"]):
        return {"intent": "WEATHER", "entity": None, "confidence": 0.95, "negated": False}


    if any(word in user.lower() for word in ["call my phone", "ring my phone", "call me", "call"]):
        return {"intent": "CALL_PHONE", "entity": None, "confidence": 0.95, "negated": False}

    # Web
    if any(word in user for word in [
        "weather", "news", "score", "stock",
        "search", "who is", "what is", "when is"
    ]):
        return {
            "intent": WEB,
            "entity": user,
            "confidence": 0.90,
            "negated": False
        }

    return {
        "intent": AI,
        "entity": user,
        "confidence": 0.80,
        "negated": False
    }



def is_multistep_task(user_input: str) -> bool:
    """Detect whether user input implies an autonomous multi-step workflow."""
    indicators = [
        r"\band\s+then\b",
        r"\bafter\s+that\b",
        r"\bcreate\b.*\band\b",
        r"\bopen\b.*\band\b",
        r"\bworkflow\b",
        r"\bplan\b",
        r"\bprepare\s+workspace\b"
    ]
    lowered = user_input.lower().strip()
    return any(re.search(pattern, lowered) for pattern in indicators)


def route_input(
    user_input: str,
    speak_callback: Callable[[str], None],
    status_callback: Optional[Callable[[str], None]] = None,
    confirm_callback: Optional[Callable[[str], bool]] = None
) -> str:
    """Main routing function for voice and text commands."""
    clean_input = user_input.strip()

    # Route 1: Autonomous Multi-Step Engine
    if is_multistep_task(clean_input):
        speak_callback("Planning the task now.")
        
        try:
            plan = planner.plan(clean_input)
            engine = TaskExecutionEngine(step_timeout_seconds=8, confirm_callback=confirm_callback)
            
            result = engine.execute_plan(plan, status_callback=status_callback)
            
            # Speak and return the truthful summary
            speak_callback(result["summary"])
            return result["summary"]
        except Exception as e:
            err_msg = f"Task engine encountered a planning error: {str(e)}"
            speak_callback(err_msg)
            return err_msg

    # Route 2: Preserve Existing Local Single Commands
    # (Hook into your existing commands.py dispatcher here)
    # from commands import handle_direct_command
    # if handle_direct_command(clean_input):
    #     return "Handled locally."

    # Route 3: Standard Conversational Fallback
    # (Hook into your existing ai.py chat completion)
    # response = chat_with_groq(clean_input)
    # speak_callback(response)
    # return response
    return "Handled via default conversation."