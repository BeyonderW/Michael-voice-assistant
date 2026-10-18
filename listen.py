import speech_recognition as sr

r = sr.Recognizer()

def listen():
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                audio = r.listen(source)

            print("Recognizing...")
            user = r.recognize_google(audio, language="en-IN")
            print("You:", user)
            return user

        except sr.UnknownValueError:
            print("Didn't catch that.")
            continue

        except sr.RequestError:
            print("Speech recognition unavailable.")
            continue