import json
from pathlib import Path

hitsounds_dir = Path("hitsounds/")

with open(hitsounds_dir / "hitsounds_new.json") as f:
  data = json.load(f)

for key, v in data.items():
  for item in v:
    t = item["type"]
    if t == "hs-filter-tab":
      item["type"] = "hs"
    else:
      item["type"] = "ks"

with open(hitsounds_dir / "hitsounds_types.json", "w") as f:
  json.dump(data, f, indent=2)
