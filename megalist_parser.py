import json
import httpx
import markdown
import shutil
import subprocess
import urllib.request
import os
import re
from lxml import etree
from pathlib import Path
from collections import defaultdict
from PIL import Image

# get megalist from github
megalist = httpx.get("https://raw.githubusercontent.com/Hypnootize/TF2-HUDs-Megalist/master/Active%20Huds%20List.md").text

# split it up to iterate through the lines until we find the table
megalist = megalist.splitlines()

table_start = 0

for n in range(len(megalist)):
  if "|" in megalist[n] and "-" in megalist[n + 1]:
    table_start = n
    break

megalist = "\n".join(megalist[table_start:])

input_data = Path("input")
input_huds = defaultdict(dict)
if input_data.exists():
  for f in input_data.glob("*.json"):
    with open(f) as file:
      input_huds[f.stem] = json.load(file)

huds = []

for n, line in enumerate(megalist.split('\n')):
    data = {}
    if n == 0:
        header = [t.strip() for t in line.split('|')]
    if n > 1:
        values = [t.strip() for t in line.split('|')]
        for col, value in zip(header, values):
            data[col] = value
        huds.append(data)


def get_doc(text):
  return etree.fromstring(markdown.markdown(text))


def get_links(text):
  doc = get_doc(text)
  links = {}
  for link in doc.xpath('//a'):
    links[link.text] = link.get('href')
  return links


def get_authors(text):
  doc = get_doc(text)
  authors = []
  for author in doc.xpath('//em'):
    authors.append(author.text)
  for author in doc.xpath('//code'):
    if author.text == "Unknown":
      continue
    authors.append(author.text)
  return ", ".join(authors)

hud_data = {}

for hud in huds:
  hud_name = hud["HUD Name"]

  # Check for repo first
  repo_links = get_links(hud["Repository"]) if hud["Repository"] else None
  repo = repo_links["GitHub"] if repo_links and "GitHub" in repo_links else None
  if not repo:
    print(f"HUD {hud_name} has no repo, skipping")
    continue

  if repo.endswith("/"):
    repo = repo[:-1]
  if repo.endswith(".git"):
    repo = repo[:-4]

  # Get the rest of the data
  hud_id = hud_name.lower().replace(" ", "-")
  hud_id = re.sub(r'-+', "-", hud_id)
  author = get_authors(hud["`Creator` & *Maintainer*"])
  steam_group = get_links(hud["Steam Group"])["Steam"].replace("https://steamcommunity.com/groups/", "") if hud["Steam Group"] else None
  discord = get_links(hud["Discord"])["Discord"].replace("https://discord.gg/", "") if hud["Discord"] else None

  # must have screenshots, in practice only the default HUDs listed don't
  if not hud["Screens"]:
    continue

  image_links = get_links(hud["Screens"])
  album = image_links["Album"] if "Album" in image_links else image_links["Screen"]

  # Conditionally build the data
  hud_meta_in = input_huds[hud_id]
  if hud_meta_in.get("social"):
    hud_meta = hud_meta_in
  else:
    hud_meta = {}
    hud_meta["name"] = hud_name
    hud_meta["author"] = author
    hud_meta["social"] = {}
    if steam_group:
      hud_meta["social"]["steam_group"] = steam_group
    if discord:
      hud_meta["social"]["discord"] = discord
    hud_meta["repo"] = repo
    hud_meta["hash"] = ""
    if hud_meta_in.get("parent"):
      hud_meta["parent"] = hud_meta_in["parent"]
    hud_meta["resources"] = []

  if album:
      hud_meta["social"]["album"] = album

  for key, value in hud_meta_in.items():
    if key == "social":
      continue
    hud_meta[key] = value

  hud_data[hud_id] = hud_meta

output = Path("./output/")
output.mkdir(exist_ok=True)
data_out = output / "data"
data_out.mkdir(exist_ok=True)
data_res = output / "resources"
data_res.mkdir(exist_ok=True)


for hud_id, hud in hud_data.items():
  hud_data_path = data_out / f"{hud_id}.json"

  if hud_data_path.exists():
    continue

  hud["resources"] = hud["resources"] or [f"{hud_id}-banner"]

  hud["hash"] = hud["hash"] or subprocess.check_output(["git", "ls-remote", hud["repo"], "HEAD"]).decode("utf-8").split()[0]

  with open(hud_data_path, "w") as f:
    json.dump(hud, f, indent=2)

imgur_client_id = os.getenv("IMGUR_CLIENT_ID")
imgur_headers = {
  'Authorization': 'Client-ID ' + imgur_client_id,
  'Accept': 'application/json'
}

def download_img(url, folder, final_path):
  img_name = url.split('/')[-1]
  img_path = folder / img_name
  urllib.request.urlretrieve(url, img_path)
  im = Image.open(img_path).convert("RGB")
  img_path.unlink()
  im.save(folder / f"{final_path}.webp", quality=75)

for hud_id, hud in hud_data.items():
  data_res_id = data_res / hud_id
  final_res_path = data_res_id
  if final_res_path.exists():
    continue
  data_res_id.mkdir()

  res = hud["social"]["album"]

  # download the img
  if "camo.githubusercontent.com" in res or "i.imgur.com" in res:
    img_url = res
    # single img, not an album
    del hud["social"]["album"]
    download_img(img_url, data_res_id, f"{hud_id}-banner")
  elif "imgur.com/a/" in res or "imgur.com/gallery/" in res or "imgur.com/album/" in res:
    res = res.replace("imgur.com/a/", "imgur.com/album/").replace("imgur.com/gallery/", "imgur.com/album/")
    imgur_res = "/".join(res.split("/")[-2:])
    imgur_resp = httpx.get(f"https://api.imgur.com/3/{imgur_res}", headers=imgur_headers)
    try:
      imgur_data = imgur_resp.json()
    except Exception:
      print(res)
      print(f"Failed to get imgur data for {hud_id}: {imgur_resp.text}")
      raise
    images = imgur_data["data"]["images"]
    for idx in range(min(4, len(images))):
      img_link = images[idx]["link"]
      if idx == 0:
        download_img(img_link, data_res_id, f"{hud_id}-banner")
      elif False:
        res_name = f"{hud_id}-{idx}"
        hud["resources"].append(res_name)
        download_img(img_link, data_res_id, res_name)
      
    if False:
      hud_data_path = data_out / f"{hud_id}.json"

      with open(hud_data_path, "w") as f:
        json.dump(hud, f, indent=2)
  else:
    print(f"Unknown resource type for {hud_id}: {res}")
    continue

  