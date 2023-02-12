import hashlib
import json
import shutil
from pathlib import Path

hitsounds_dir = Path("hitsounds/")

hitsounds_dir_old = Path("hitsounds/finalv1")

hitsounds_dir_new = Path("hitsounds/finalv2")

with open(hitsounds_dir / "hitsounds.json") as f:
  data = json.load(f)

for file in hitsounds_dir_old.glob("*.wav"):
  file_contents = file.read_bytes()
  old_hash = file.stem
  if old_hash not in data:
    print(f"Skipping {file.name}... (not in hitsounds.json)")
    continue
  h = hashlib.blake2b(file_contents).hexdigest()
  shutil.copy(file, hitsounds_dir_new / f"{h}.wav")
  if old_hash != h:
    #print(f"Updating {file.name}...")
    data[h] = data[old_hash]
    del data[old_hash]

with open(hitsounds_dir / "hitsounds_new.json", "w") as f:
  json.dump(data, f, indent=2)
