import time
import httpx
import lxml.html
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from timeit import default_timer as timer

hitsound_pages = list(range(2, 157))

hitsound_urls = ["https://huds.tf/site/d-Hitsound"]
hitsound_urls.extend([f"https://huds.tf/site/d-Hitsound?page={page}" for page in hitsound_pages])

hitsounds_dir = Path("hitsounds")
hitsounds_dir.mkdir(exist_ok=True)

data = defaultdict(list)

budget = 0.1
last = timer()

def req_url(url):
  global last
  now = timer()
  if now - last < budget:
    time.sleep(budget - (now - last))
  return httpx.get(url)

types = {
  "hs-filter-tab": "hitsound",
  "ks-filter-tab": "killsound"
}

for url in hitsound_urls:
  page_text = req_url(url).text
  types = lxml.html.fromstring(page_text).xpath("//div[@class='huds-directory']/a/@class")
  sound_ids = lxml.html.fromstring(page_text).xpath("//p[@class='huds-directory-item-name']/a/@href")
  titles = lxml.html.fromstring(page_text).xpath("//p[@class='huds-directory-item-name']/a/text()")
  links = lxml.html.fromstring(page_text).xpath("//a[@class='huds-directory-download-hts']/@href")
  for i in range(len(links)):
    link = links[i]
    link = f"https://huds.tf/site/{link}"
    file_contents = req_url(link).content
    h = hashlib.blake2b(file_contents).hexdigest()
    data[h].append({
      "title": titles[i],
      "id": sound_ids[i],
      "type": types[i]
    })
    file_path = hitsounds_dir / f"{h}.wav"
    if not file_path.exists():
      file_path.write_bytes(file_contents)

with open(hitsounds_dir / "hitsounds.json", "w") as f:
  json.dump(data, f, indent=2)
