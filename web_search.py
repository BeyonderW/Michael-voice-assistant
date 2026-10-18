from ddgs import DDGS

def web_search(query):
    with DDGS() as ddgs:
        results = list(ddgs.text(query,max_results=5))

    if not results:
        return "NO results found."
    

    return results

     