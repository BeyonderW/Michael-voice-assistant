import speech_recognition as sr

from app_search import INSTALLED_APPS
from stt_correction import pick_best

r = sr.Recognizer()


def _window_titles():
    try:
        import pygetwindow as gw
        return [t for t in gw.getAllTitles() if t]
    except Exception:
        return []


def _recognize(audio):
    """Asks Google for alternatives and picks the one that best fits installed apps."""
    result = r.recognize_google(audio, language="en-IN", show_all=True)

    if not result or "alternative" not in result:
        raise sr.UnknownValueError()

    transcripts = [
        alt["transcript"] for alt in result["alternative"] if alt.get("transcript")
    ]

    if not transcripts:
        raise sr.UnknownValueError()

    chosen = pick_best(transcripts, INSTALLED_APPS.keys(), _window_titles())

    if chosen != transcripts[0]:
        print(f"(corrected '{transcripts[0]}' -> '{chosen}')")

    return chosen


def listen(timeout=None):
    """
    timeout=None  -> keep trying until something is understood.
    timeout=N     -> return None if nobody starts speaking within N seconds,
                     or if the speech couldn't be understood (hotkey mode).
    """
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                audio = r.listen(source, timeout=timeout, phrase_time_limit=15)

            print("Recognizing...")
            user = _recognize(audio)
            print("You:", user)
            return user

        except sr.WaitTimeoutError:
            if timeout is not None:
                return None
            continue

        except sr.UnknownValueError:
            print("Didn't catch that.")
            if timeout is not None:
                return None
            continue

        except sr.RequestError:
            print("Speech recognition unavailable.")
            if timeout is not None:
                return None
            continue