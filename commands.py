import os
import subprocess
import psutil
import requests
import pygetwindow as gw
from datetime import datetime
from web_search import web_search
from file_search import search_files
from app_search import get_installed_apps
from process_man import track_launch, close_by_pid

installed_apps = get_installed_apps()

# Known Windows system utilities that often don't show up reliably
# in Start Menu shortcut scans or Get-StartApps
SYSTEM_UTILITIES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "registry editor": "regedit.exe",
    "snipping tool": "snippingtool.exe",
    "character map": "charmap.exe",
    "magnifier": "magnify.exe",
}


def get_time():
    return f" The current time is {datetime.now().strftime('%I:%M %p')}"


def get_date():
    return f"Today's date is {datetime.now().strftime('%d %B %Y')}"


def _launch(app_name):
    """Actually performs the launch. Returns a result string or None."""

    # Try Microsoft Store / registered apps first
    ps = rf'''
$app = Get-StartApps | Where-Object {{ $_.Name -like "*{app_name}*" }} | Select-Object -First 1
if ($app) {{
    Start-Process "shell:AppsFolder\$($app.AppID)"
    exit 0
}}
exit 1
'''

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return f"Opening {app_name}"

    # Fallback to desktop apps
    for name, path in installed_apps.items():
        if app_name in name:
            os.startfile(path)
            return f"Opening {name}"

    # Fallback to known Windows system utilities
    for name, exe in SYSTEM_UTILITIES.items():
        if app_name in name or name in app_name:
            subprocess.Popen(exe)
            return f"Opening {name}"

    return None


def open_installed_app(app_name):
    app_name = app_name.lower().strip()

    result = track_launch(app_name, lambda: _launch(app_name))

    if result:
        return result

    return f"I couldn't find {app_name}."


def _close_by_window_title(app_name):
    """
    Closes any open window whose title contains app_name.
    Handles apps that don't run as a distinct process (e.g. PWAs
    like Netflix running inside msedge.exe) by targeting the
    specific window instead of the shared browser process.
    """
    try:
        titles = gw.getAllTitles()
    except Exception:
        return False

    for title in titles:
        if not title:
            continue

        if app_name in title.lower():
            try:
                win = gw.getWindowsWithTitle(title)[0]
                win.close()
                return True
            except Exception:
                continue

    return False


def close_app(app_name):
    app_name = app_name.lower().strip()

    # Close using tracked PID (exact, reliable)
    if close_by_pid(app_name):
        return f"Closed {app_name}"

    # Fallback: search running processes by name
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"]

            if not name:
                continue

            process_name = name.lower().replace(".exe", "")

            if (
                app_name == process_name
                or app_name in process_name
                or process_name in app_name
            ):
                proc.terminate()
                return f"Closed {app_name}"

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Fallback: close by window title (handles PWAs / browser-hosted apps)
    if _close_by_window_title(app_name):
        return f"Closed {app_name}"

    return f"{app_name} is not running."


def find_file(file_name):
    results = search_files(file_name)

    if not results:
        return "File not found."

    os.startfile(results[0])
    return f"Opening {os.path.basename(results[0])}"


def search_web(query):
    return web_search(query)



def get_upcoming_contests():
    try:
        url = "https://www.codechef.com/api/list/contests/all"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()

        upcoming = data.get("future_contests", [])
        
        if not upcoming:
            return "There are no upcoming CodeChef contests listed right now."

        results = []
        for contest in upcoming[:3]:
            name = contest.get("contest_name")
            start = contest.get("contest_start_date")
            results.append(f"{name} on {start}")

        return "Here are the upcoming CodeChef contests to help you reach that 5-star rating: " + ", ".join(results) + "."
    
    except Exception:
        return "I couldn't reach CodeChef right now."