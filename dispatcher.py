from commands import (
    open_installed_app,
    close_app,
    get_time,
    get_date,
    find_file,
    get_upcoming_contests,
)

import pyautogui
import cv2
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_,
    CLSCTX_ALL,
    None
)

volume = cast(interface, POINTER(IAudioEndpointVolume))


def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("Screenshot.png")
    return "Screenshot taken."


def open_camera():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "I couldn't access the camera."

    ret, frame = cap.read()
    cap.release()

    if ret:
        cv2.imwrite("photo.jpg", frame)
        return "Photo captured."

    return "Failed to capture photo."


def volume_up():
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
    return "Volume increased."


def volume_down():
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
    return "Volume decreased."


def mute():
    volume.SetMute(1, None)
    return "Muted."


def unmute():
    volume.SetMute(0, None)
    return "Unmuted."


def brightness_up():
    sbc.set_brightness("+10")
    return "Brightness increased."


def brightness_down():
    sbc.set_brightness("-10")
    return "Brightness decreased."


def max_brightness():
    sbc.set_brightness(100)
    return "Brightness set to maximum."


def min_brightness():
    sbc.set_brightness(10)
    return "Brightness lowered."


handlers = {
    "OPEN_APP": open_installed_app,
    "CLOSE_APP": close_app,
    "SCREENSHOT": lambda _: take_screenshot(),
    "CAMERA": lambda _: open_camera(),
    "TIME": lambda _: get_time(),
    "DATE": lambda _: get_date(),
    "VOLUME_UP": lambda _: volume_up(),
    "VOLUME_DOWN": lambda _: volume_down(),
    "MUTE": lambda _: mute(),
    "UNMUTE": lambda _: unmute(),
    "BRIGHTNESS_UP": lambda _: brightness_up(),
    "BRIGHTNESS_DOWN": lambda _: brightness_down(),
    "MAX_BRIGHTNESS": lambda _: max_brightness(),
    "MIN_BRIGHTNESS": lambda _: min_brightness(),
    "FIND_FILE": find_file,
    "CODECHEF": lambda _: get_upcoming_contests()
}


def dispatch(intent, entity=None):
    handler = handlers.get(intent)

    if not handler:
        return None

    return handler(entity)