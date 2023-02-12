import json
import shutil
from pathlib import Path

hitsounds_dir = Path("hitsounds/")

hitsounds_dir_wav = Path("hitsounds/finalv2")

with open(hitsounds_dir / "hitsounds_types.json") as f:
  data = json.load(f)

for key, v in data.items():
  fn = f"{key}.wav"
  file = hitsounds_dir_wav / fn
  if not file.exists():
    print(f"Skipping {file.name}... (not in hitsounds/finalv2)")
    continue
  shutil.copy(file, hitsounds_dir / v[0]["type"] / fn)
