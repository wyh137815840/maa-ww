import json
from urllib.request import urlopen

data = json.load(urlopen("http://127.0.0.1:8765/api/list"))
print("needs_annotation:")
for it in data["inbox"]:
    if it.get("needs_annotation"):
        print(" ", it["name"], it.get("title"))
print("exported:")
for it in data["inbox"]:
    if it.get("exported"):
        print(" ", it["name"], "->", it.get("exported_card_id"))
