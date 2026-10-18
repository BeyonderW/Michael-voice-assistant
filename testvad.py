import sounddevice as sd
import numpy as np

print("speak for 5 sec...")
audio = sd.rec(
    int(5*16000),
    samplerate=16000,
    channels=1,
    dtype='float32'

)
sd.wait
print("Recording finished")
print(audio.shape)
