#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
screen = Image.open(root / "review/cards/20261031-194335-tacetstartchallenge/screen.png").convert("RGB")
cx, cy = 1094, 661
# tight crop around 开启挑战 button
w, h = 160, 48
x1 = max(0, cx - w // 2)
y1 = max(0, cy - h // 2)
x2 = min(1280, x1 + w)
y2 = min(720, y1 + h)
crop = screen.crop((x1, y1, x2, y2))
out = root / "assets/resource_adb/image/Guidebook/TacetStartChallenge.png"
crop.save(out)
print("roi", [x1, y1, x2 - x1, y2 - y1], "->", out)
