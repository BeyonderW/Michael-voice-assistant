import os
import subprocess
import re
from rapidfuzz import process, fuzz

# Known Windows system utilities that don't reliably show up in
# Start Menu shortcut scans or Get-StartApps, but should still be
# matchable by name (notepad, calculator, etc.)
SYSTEM_UTILITIES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "registry editor": "regedit.exe",
    "snipping tool": "snippingtool.exe",
    "character map": "charmap.exe",
    "magnifier": "magnify.exe",
}


def get_installed_apps():
    app_paths = {}

    start_menu_locations = [
        os.path.join(os.environ["ProgramData"],
                     r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ["APPDATA"],
                     r"Microsoft\Windows\Start Menu\Programs")
    ]

    for location in start_menu_locations:
        for root, _, files in os.walk(location):
            for file in files:
                if file.endswith(".lnk"):
                    app_name = os.path.splitext(file)[0].lower()
                    app_paths[app_name] = os.path.join(root, file)

    # Add Microsoft Store apps
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json"
            ],
            capture_output=True,
            text=True
        )

        import json

        apps = json.loads(result.stdout)

        if isinstance(apps, dict):
            apps = [apps]

        for app in apps:
            name = app["Name"].lower()
            appid = app["AppID"]
            app_paths[name] = f"shell:AppsFolder\\{appid}"

    except Exception:
        pass

    # Merge in known system utilities so they're matchable even if
    # they weren't picked up by the scans above
    for name, exe in SYSTEM_UTILITIES.items():
        if name not in app_paths:
            app_paths[name] = exe

    return app_paths


# Cache installed apps
INSTALLED_APPS = get_installed_apps()


def find_best_app(user_input):
    user_input = user_input.lower()

    for word in ["open", "launch", "start", "run", "close", "quit", "exit", "terminate", "kill"]:
        user_input = user_input.replace(word, "")

    user_input = user_input.strip()

    match = process.extractOne(
        user_input,
        INSTALLED_APPS.keys(),
        scorer=fuzz.partial_ratio,
        score_cutoff=60
    )

    if match:
        return match[0]

    return None


if __name__ == "__main__":
    apps = get_installed_apps()
    print(f"Found {len(apps)} store apps:\n")

    for app in sorted(apps):
        print(app)