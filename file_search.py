import os
import concurrent.futures

SEARCH_FOLDERS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Videos"),
    os.path.expanduser("~/Music"),
]

def _search_directory(folder, filename):
    for root, _, files in os.walk(folder):
        for file in files:
            if filename in file.lower():
                return os.path.join(root, file)
    return None

def search_files(filename):
    filename = filename.lower()
    valid_folders = [f for f in SEARCH_FOLDERS if os.path.exists(f)]
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(_search_directory, folder, filename) for folder in valid_folders]
        
        for future in concurrent.futures.as_completed(futures):
            match = future.result()
            if match:
                return [match]
                
    return []