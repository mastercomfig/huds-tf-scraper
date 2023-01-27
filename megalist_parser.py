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
  resource = image_links["Album"] if "Album" in image_links else image_links["Screen"]

  # Conditionally build the data
  hud_meta = {}
  hud_meta["name"] = hud_name
  hud_meta["author"] = author
  if steam_group or discord:
    hud_meta["social"] = {}
    if steam_group:
      hud_meta["social"]["steam_group"] = steam_group
    if discord:
      hud_meta["social"]["discord"] = discord
  hud_meta["repo"] = repo
  hud_meta["hash"] = ""
  hud_meta["resources"] = resource
  hud_data[hud_id] = hud_meta

output = Path("./output/")
output.mkdir(exist_ok=True)
data_out = output / "data"
data_out.mkdir(exist_ok=True)
data_res = output / "resources"
data_res.mkdir(exist_ok=True)

hud_res = {}

for hud_id, hud in hud_data.items():
  hud_data_path = data_out / f"{hud_id}.json"

  res = hud["resources"]
  hud_res[hud_id] = res

  if hud_data_path.exists():
    continue

  hud["resources"] = [f"{hud_id}-banner"]

  hud["hash"] = subprocess.check_output(["git", "ls-remote", hud["repo"], "HEAD"]).decode("utf-8").split()[0]

  with open(hud_data_path, "w") as f:
    json.dump(hud, f, indent=2)

imgur_client_id = os.getenv("IMGUR_CLIENT_ID")
imgur_headers = {
  'Authorization': 'Client-ID ' + imgur_client_id,
  'Accept': 'application/json'
}

for hud_id, hud in hud_data.items():
  data_res_id = data_res / hud_id
  data_res_id.mkdir(exist_ok=True)

  final_res_path = data_res_id / f"{hud_id}-banner.webp"
  if final_res_path.exists():
    continue

  res = hud_res[hud_id]

  # download the img
  if "camo.githubusercontent.com" in res or "i.imgur.com" in res:
    img_url = res
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
    img_url = images[0]["link"]
  else:
    print(f"Unknown resource type for {hud_id}: {res}")
    continue

  img_name = img_url.split('/')[-1]
  img_path = data_res_id / img_name
  urllib.request.urlretrieve(img_url, img_path)
  im = Image.open(img_path).convert("RGB")
  img_path.unlink()
  im.save(final_res_path, quality=75)
