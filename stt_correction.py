import re
from rapidfuzz import process, fuzz

ACTION_WORDS = {"open", "launch", "start", "run", "close", "quit", "exit", "terminate", "kill"}
CLOSE_WORDS = {"close", "quit", "exit", "terminate", "kill"}

APP_MATCH_CUTOFF = 75      # minimum score to treat a phrase as "an app command"
SWITCH_CUTOFF = 85         # how good an alternative must be to replace a non-app top guess


def _squash(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _is_close(text):
    return any(w in CLOSE_WORDS for w in text.lower().split())


def _match_app(text, squashed_apps):
    """Returns (squashed_app_name, score) for a phrase like 'close onenote', else (None, 0)."""
    words = text.lower().split()

    if not any(w in ACTION_WORDS for w in words):
        return None, 0

    query = _squash("".join(w for w in words if w not in ACTION_WORDS))

    if not query:
        return None, 0

    match = process.extractOne(
        query, squashed_apps, scorer=fuzz.WRatio, score_cutoff=APP_MATCH_CUTOFF
    )

    return (match[0], match[1]) if match else (None, 0)


def _has_window(app, titles):
    return any(app in t or (len(t) >= 5 and t in app) for t in titles)


def pick_best(alternatives, app_names, window_titles=()):
    """
    alternatives: Google's transcripts, its first choice first.
    app_names:    installed app names (the keys of INSTALLED_APPS).
    window_titles: titles of currently open windows.
    Returns the transcript Michael should act on.
    """
    if not alternatives:
        return None

    squashed_apps = [_squash(n) for n in app_names]
    titles = [_squash(t) for t in window_titles if t]

    info = []
    for text in alternatives:
        app, score = _match_app(text, squashed_apps)
        info.append((text, app, score))

    top_text, top_app, top_score = info[0]

    # Case 1: Google's first guess is already a real app command.
    # Only reconsider for CLOSE commands: if another near-equal alternative names
    # an app that has a visible window, the user most likely meant that one
    # (e.g. "close onedrive" vs "close one note" while OneNote is open).
    if top_app:
        if _is_close(top_text):
            for text, app, score in info:
                if (
                    app
                    and _is_close(text)
                    and score >= top_score - 5
                    and _has_window(app, titles)
                ):
                    return text
        return top_text

    # Case 2: first guess isn't a recognisable app command (e.g. "close asfa").
    # Switch only if an alternative is clearly a real app command.
    best = max(info[1:], key=lambda x: x[2], default=None)

    if best and best[2] >= SWITCH_CUTOFF:
        return best[0]

    return top_text