from app_search import find_best_app


def extract_app(user):
    return find_best_app(user)


def extract_file(user):
    words = user.split()

    if "find" in words:
        index = words.index("find")

        if index + 1 < len(words):
            return " ".join(words[index + 1:])

    return None