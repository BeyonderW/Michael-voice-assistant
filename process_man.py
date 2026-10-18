import time
import subprocess
import re
import psutil

# app_name (lowercase) -> pid
running_apps = {}


def _normalize(name):
    """Strips spaces/punctuation so 'asphalt 8: airborne' ~= 'asphalt8'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _snapshot_pids():
    return set(psutil.pids())


def _find_matching_new_pid(app_name, before_pids, poll_seconds=6.0, interval=0.5):
    """
    Polls for new processes over time and returns the PID of the
    first NEW process whose name resembles app_name. Never guesses
    a random unrelated PID.
    """
    target = _normalize(app_name)
    elapsed = 0.0

    print(f"[DEBUG] Watching for process matching normalized target: '{target}'")

    while elapsed < poll_seconds:
        time.sleep(interval)
        elapsed += interval

        after = _snapshot_pids()
        new_pids = after - before_pids

        for pid in new_pids:
            try:
                proc = psutil.Process(pid)
                proc_name = _normalize(proc.name().replace(".exe", ""))

                if not proc_name:
                    continue

                print(f"[DEBUG] New process seen: pid={pid} raw='{proc.name()}' normalized='{proc_name}'")

                if target in proc_name or proc_name in target:
                    print(f"[DEBUG] MATCH found: pid={pid}")
                    return pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    print(f"[DEBUG] No match found for '{target}' after {poll_seconds}s of polling")
    return None


def track_launch(app_name, launch_fn, poll_seconds=6.0):
    """
    Runs launch_fn() (which should actually start the app),
    then polls for a new process whose name matches app_name and
    stores its PID. If nothing matches, tracks nothing (so close_app
    falls back to name-based matching instead of killing the wrong
    process). Returns launch_fn()'s return value.
    """
    app_name = app_name.lower().strip()

    before = _snapshot_pids()

    result = launch_fn()

    pid = _find_matching_new_pid(app_name, before, poll_seconds=poll_seconds)

    if pid is not None:
        running_apps[app_name] = pid
        print(f"[DEBUG] Tracked '{app_name}' -> PID {pid}")
    else:
        print(f"[DEBUG] Nothing tracked for '{app_name}'")

    return result


def is_running(app_name):
    app_name = app_name.lower().strip()

    pid = running_apps.get(app_name)

    if pid is None:
        return False

    if not psutil.pid_exists(pid):
        del running_apps[app_name]
        return False

    return True


def close_by_pid(app_name):
    """
    Attempts to close a tracked app by its stored PID using taskkill
    (kills the full process tree - more reliable than psutil terminate()
    for Store/UWP apps and multi-process apps like browsers).
    Returns True if it actually closed, False if nothing was tracked
    or the process is still alive afterward (caller should fall back
    to name-based matching).
    """
    app_name = app_name.lower().strip()

    print(f"[DEBUG] close_by_pid called for '{app_name}'. Currently tracked: {running_apps}")

    pid = running_apps.get(app_name)

    if pid is None:
        print(f"[DEBUG] No tracked PID for '{app_name}'")
        return False

    if not psutil.pid_exists(pid):
        print(f"[DEBUG] Tracked PID {pid} no longer exists")
        del running_apps[app_name]
        return False

    try:
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True,
            text=True
        )
        print(f"[DEBUG] taskkill stdout: {result.stdout.strip()} stderr: {result.stderr.strip()}")
    except Exception as e:
        print(f"[DEBUG] taskkill exception: {e}")

    del running_apps[app_name]

    # Confirm it's actually gone before claiming success
    time.sleep(0.5)

    if psutil.pid_exists(pid):
        print(f"[DEBUG] PID {pid} still alive after taskkill")
        return False

    print(f"[DEBUG] PID {pid} confirmed closed")
    return True


def cleanup_dead():
    """Remove entries whose PID no longer exists. Call periodically."""
    dead = [
        name for name, pid in running_apps.items()
        if not psutil.pid_exists(pid)
    ]

    for name in dead:
        del running_apps[name]