import wave
from pathlib import Path

sounds = Path("hitsounds/lowsamples").glob("*.wav")

low_freq = 0

for sound in sounds:
  try:
    with wave.open(str(sound), "rb") as wav:
      if wav.getframerate() < 44100:
        print(f"{sound}")
        low_freq += 1
  except wave.Error:
    pass
