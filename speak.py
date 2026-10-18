import edge_tts
import pygame
import os
import time
import threading
import speech_recognition as sr

_interrupt_flag = threading.Event()


def _watch_for_interrupt():
    r = sr.Recognizer()
    r.dynamic_energy_threshold = False

    try:
        with sr.Microphone() as source:
            # Calibrate WHILE audio is already playing, so speaker
            # bleed picked up by the mic becomes the baseline, not
            # something that triggers a false interrupt.
            r.adjust_for_ambient_noise(source, duration=1.0)
            r.energy_threshold += 400  # margin above playback volume

            while pygame.mixer.music.get_busy() and not _interrupt_flag.is_set():
                try:
                    r.listen(source, timeout=1, phrase_time_limit=1)
                    _interrupt_flag.set()
                    pygame.mixer.music.stop()
                    break
                except sr.WaitTimeoutError:
                    continue
    except Exception:
        pass


async def speak(text, allow_interrupt=True):
    _interrupt_flag.clear()

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    if os.path.exists("voice.mp3"):
        os.remove("voice.mp3")

    communicate = edge_tts.Communicate(
        text,
        voice="en-GB-RyanNeural"
    )

    await communicate.save("voice.mp3")

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load("voice.mp3")
    pygame.mixer.music.play()

    if allow_interrupt:
        # Give playback a moment to actually start before the watcher
        # calibrates against it
        time.sleep(0.4)
        watcher = threading.Thread(target=_watch_for_interrupt, daemon=True)
        watcher.start()

    while pygame.mixer.music.get_busy():
        pass

    _interrupt_flag.set()