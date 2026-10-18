import re
import spacy
from intent import *
from entities import extract_app, extract_file

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