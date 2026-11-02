import re
import webbrowser
from urllib.parse import urlparse
from rapidfuzz import process, fuzz

KNOWN_SITES = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "google maps": "https://maps.google.com",
    "google drive": "https://drive.google.com",
    "github": "https://github.com",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "reddit": "https://www.reddit.com",
    "stack overflow": "https://stackoverflow.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "claude": "https://claude.ai",
}

# words that carry no site-name information
FILLER = {
    "open", "launch", "start", "go", "to", "visit", "browse", "the", "website",
    "site", "web", "page", "please", "take", "me", "michael", "on", "in", "my",
    "browser",
}

DOMAIN_RE = re.compile(r"\b[a-z0-9-]+\.(?:com|org|net|in|io|edu|co|dev|ai|app)\b")


def _squash(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def extract_website(user):
    """Returns a URL for 'open youtube' / 'go to github.com', else None."""
    text = user.lower()

    # explicit domain, e.g. "open github.com"
    match = DOMAIN_RE.search(text)
    if match:
        return "https://" + match.group(0)

    words = [w for w in re.findall(r"[a-z0-9]+", text) if w not in FILLER]

    # long sentences are conversation, not "open <site>"
    if not words or len(words) > 3:
        return None

    query = "".join(words)
    names = {_squash(n): n for n in KNOWN_SITES}

    best = process.extractOne(query, names.keys(), scorer=fuzz.WRatio, score_cutoff=80)

    return KNOWN_SITES[names[best[0]]] if best else None


def open_website(url):
    webbrowser.open(url)
    host = urlparse(url).netloc.replace("www.", "")
    return f"Opening {host}"