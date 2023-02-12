import subprocess
from pathlib import Path

sounds = Path("hitsounds/testmono").glob("*.wav")

for sound in sounds:
  try:
    output = subprocess.getoutput(f"ffmpeg -i {sound} -filter_complex 'stereotools=phasel=1[tmp];[tmp]pan=1c|c0=0.5*c0+0.5*c1,volumedetect' -f null /dev/null").splitlines()
    for line in output:
      if "volumedetect:default has an unconnected output" in line:
        print(sound)
        break
      elif "mean volume:" in line:
        if "-inf dB" in line:
          print(sound)
          break
        else:
          try:
            db = float(line.split("mean volume: ")[1].split(" dB")[0])
            if db < -91.0:
              print(sound)
              break
          except:
            pass
  except:
    print(sound)
