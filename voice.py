import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=1)
    print("Listening...")
    audio = r.listen(source)

print("Recognizing...")
user = r.recognize_google(audio, language="en-IN")
print("You:",user)