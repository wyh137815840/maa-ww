#!/usr/bin/env python3
"""Sample color of 60 / 120 digits on claim dialogs."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
inbox = root / "review/inbox"
for name in [
    "20261031-201915-tacet-stamina.png",
    "20261031-201919-snap.png",
    "20261031-202033-snap.png",
]:
    p = inbox / name
    if not p.is_file():
        print("missing", name)
        continue
    im = Image.open(p).convert("RGB")
    # Approximate centers of the cost numbers on the two buttons
    # Left 60 ~ (520, 400), Right 120 ~ (740, 400) — dialog centered
    samples = {
        "60_area": (520, 400),
        "120_area": (740, 400),
        "60b": (500, 405),
        "120b": (760, 405),
        "60c": (535, 398),
        "120c": (725, 398),
    }
    print(name, im.size)
    for k, (x, y) in samples.items():
        print(f"  {k}@({x},{y}) = {im.getpixel((x, y))}")

# list newest cards dirs by mtime
cards = root / "review/cards"
dirs = sorted(cards.glob("2026*"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
print("newest cards:")
for d in dirs:
    cj = d / "card.json"
    if cj.is_file():
        import json
        c = json.loads(cj.read_text(encoding="utf-8"))
        print(d.name, c.get("label"), c.get("created_at"))
