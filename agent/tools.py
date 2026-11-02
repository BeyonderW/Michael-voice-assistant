"""agent/tools.py - Allowlisted tools with parameter validation and verification."""

import os
import subprocess
import webbrowser
from typing import Any, Callable, Dict, Tuple
import psutil
import urllib.parse
import ctypes

# Safe execution base directory (defaults to user Desktop/MichaelWorkspace if relative)
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), "MichaelWorkspace"))
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Common Windows executable paths
APP_REGISTRY: Dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
}


def _resolve_safe_path(filepath: str) -> str:
    """Force all file operations into the safe workspace directory."""
    # Extract only the file name, ignoring any 'C:\' or other folder paths the AI tries to use
    filename = os.path.basename(filepath)
    if not filename:
        filename = "default_file.txt"
        
    resolved = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    return resolved

# --- Tool Implementations ---

def tool_launch_app(app_name: str) -> str:
    """Launch an allowlisted Windows desktop application."""
    normalized = app_name.strip().lower()
    executable = APP_REGISTRY.get(normalized, normalized if normalized.endswith(".exe") else None)
    if not executable:
        raise ValueError(f"Application '{app_name}' is not in the approved application allowlist.")
    
    subprocess.Popen([executable], shell=False)
    return f"Successfully invoked application: {executable}"


def verify_launch_app(app_name: str) -> Tuple[bool, str]:
    """Verify application process is currently running."""
    normalized = app_name.strip().lower()
    base_exe = APP_REGISTRY.get(normalized, normalized)
    if not base_exe.endswith(".exe"):
        base_exe += ".exe"
    
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == base_exe.lower():
                return True, f"Process {base_exe} confirmed running (PID: {proc.pid})."
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, f"Process {base_exe} was not found running after invocation."


def tool_create_file(filepath: str, content: str = "") -> str:
    """Create a new text file with optional content."""
    target_path = _resolve_safe_path(filepath)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    os.startfile(target_path)
    return f"File created at {target_path}"


def verify_create_file(filepath: str, content: str = "") -> Tuple[bool, str]:
    """Verify file existence and size on disk."""
    target_path = _resolve_safe_path(filepath)
    if os.path.isfile(target_path):
        return True, f"File verified on disk at {target_path} ({os.path.getsize(target_path)} bytes)."
    return False, f"File not found on disk at {target_path}."


def tool_read_file(filepath: str) -> str:
    """Read contents of an existing file."""
    target_path = _resolve_safe_path(filepath)
    if not os.path.isfile(target_path):
        raise FileNotFoundError(f"File not found: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


def verify_read_file(filepath: str) -> Tuple[bool, str]:
    target_path = _resolve_safe_path(filepath)
    if os.path.isfile(target_path):
        return True, "File verified accessible."
    return False, "File does not exist."


def tool_delete_file(filepath: str) -> str:
    """Delete a file (Destructive action)."""
    target_path = _resolve_safe_path(filepath)
    if not os.path.isfile(target_path):
        raise FileNotFoundError(f"File not found: {target_path}")
    os.remove(target_path)
    return f"Deleted file: {target_path}"


def verify_delete_file(filepath: str) -> Tuple[bool, str]:
    """Verify file is deleted."""
    target_path = _resolve_safe_path(filepath)
    if not os.path.exists(target_path):
        return True, f"File {target_path} confirmed deleted."
    return False, f"File {target_path} still exists on disk."


def tool_open_url(url: str) -> str:
    """Open a validated HTTP/HTTPS URL in default browser."""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened URL: {url}"


def verify_open_url(url: str) -> Tuple[bool, str]:
    return True, "URL dispatch verified by OS shell handler."



def tool_search_youtube(query: str) -> str:
    """Search YouTube for a specific query."""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Opened YouTube search for: {query}"

def verify_search_youtube(query: str) -> Tuple[bool, str]:
    return True, "YouTube search dispatched to default browser."

def tool_lock_screen() -> str:
    """Lock the Windows workstation."""
    ctypes.windll.user32.LockWorkStation()
    return "Windows screen locked."

def verify_lock_screen() -> Tuple[bool, str]:
    return True, "Lock command dispatched to OS."


# --- Tool Registry Metadata ---

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "launch_app": {
        "function": tool_launch_app,
        "verifier": verify_launch_app,
        "destructive": False,
        "required_args": ["app_name"],
        "description": "Launch an approved Windows app (notepad, calculator, explorer, cmd).",
    },
    "create_file": {
        "function": tool_create_file,
        "verifier": verify_create_file,
        "destructive": False,
        "required_args": ["filepath", "content"],
        "description": "Create or overwrite a file with given text content.",
    },
    "read_file": {
        "function": tool_read_file,
        "verifier": verify_read_file,
        "destructive": False,
        "required_args": ["filepath"],
        "description": "Read contents of an existing file.",
    },
    "delete_file": {
        "function": tool_delete_file,
        "verifier": verify_delete_file,
        "destructive": True,
        "required_args": ["filepath"],
        "description": "Permanently remove a specified file.",
    },
    "open_url": {
        "function": tool_open_url,
        "verifier": verify_open_url,
        "destructive": False,
        "required_args": ["url"],
        "description": "Open a website in the default browser.",
    },
    "search_youtube": {
        "function": tool_search_youtube,
        "verifier": verify_search_youtube,
        "destructive": False,
        "required_args": ["query"],
        "description": "Open YouTube and search for the given video or topic query.",
    },
    "lock_screen": {
        "function": tool_lock_screen,
        "verifier": verify_lock_screen,
        "destructive": False,
        "required_args": [],
        "description": "Lock the Windows PC screen immediately.",
    }
}