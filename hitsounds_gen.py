import json
import urllib.parse
import codecs
from pathlib import Path

hitsounds_dir = Path("hitsounds/")

with open(hitsounds_dir / "hitsounds_types.json") as f:
  data = json.load(f)

hitsounds = []
killsounds = []

def reconcile_name(title, i):
  if not title.endswith("...") or len(title) <= 30:
    return title
  i = i[2:] # remove s-
  words = i.split("-") # split by -
  last_word = title.split(" ") # split by space
  last_word = last_word[-1][:-3] # remove ... from last word
  empty_last = last_word == ""
  last = len(words)
  found = False
  if not empty_last:
    for idx in reversed(range(last)):
      if words[idx].startswith(last_word):
        last = idx
        found = True
  title = title.split(" ")
  if not found:
    last = 0
    for title_idx in range(len(title)):
      t = title[title_idx]
      if t == "" or t == "...":
        break
      if last >= len(words):
        break
      if "..." in t:
        t = t[:-3]
      normalized = t.replace("-", "").replace("_", "").replace(".", "").replace("\"", "").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(",", "").replace("!", "").replace("?", "").replace(":", "").replace(";", "").replace("=", "").replace("+", "").replace("*", "").replace("/", "").replace("\\", "").replace("|", "").replace("~", "").replace("`", "").replace("@", "").replace("#", "").replace("$", "").replace("%", "").replace("^", "").replace("&", "").replace("<", "").replace(">", "").replace("{", "").replace("}", "")
      if words[last].startswith(normalized):
        last += 1
  words = words[last:] # remove words that are already in title
  title = title[:-1] # remove ... word
  title = " ".join(title)
  title += " " + " ".join(words)
  return title


for key, v in data.items():
  t = v[0]["type"]
  arr = hitsounds if t == "hs" else killsounds
  if len(v) == 1:
    val = v[0]
  else:
    longest = 0
    for item in v:
      if len(item["id"]) > longest:
        longest = len(item["id"])
        val = item
  
  name = reconcile_name(val["title"], val["id"])
  name = urllib.parse.unquote(name)
  if name.count("(") != name.count(")"):
    print(key, name)
  if name.count("[") != name.count("]"):
    print(key, name)
  if name.count("\"") % 2 != 0:
    print(key, name)
  arr.append({
    "name": name,
    "hash": key,
  })

data = {}
data["hitsounds"] = hitsounds
data["killsounds"] = killsounds


with open(hitsounds_dir / "hitsounds_gen.json", "w") as f:
  json.dump(data, f, indent=2)
