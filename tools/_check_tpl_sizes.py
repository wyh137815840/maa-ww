#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
paths = [
    "assets/resource_adb/image/Explore/HUD_Minimap.png",
    "assets/resource_adb/image/Guidebook/OpenGuidebook.png",
    "assets/resource_adb/image/Title/ClickConnect.png",
    "review/cards/20261031-173521-explorehud/template.png",
]
for p in paths:
    im = Image.open(ROOT / p)
    print(f"{p}: {im.size} {im.mode}")

# ROI sizes from pipeline
print("ExploreHUD roi 144x122; OpenGuidebook roi 120x90; Title roi 228x90")
