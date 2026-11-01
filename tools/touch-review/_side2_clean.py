#!/usr/bin/env python3
"""Dismiss popup → click left-rail #2 (swords) → if needed click 无音清剿 → scroll test."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402
from tacet_select_proto import detect_bar_top, find_go_buttons, plan  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "review/inbox"


def adb(cfg, *args, check=True):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def tap(cfg, x, y, wait=1.2):
    print(f"  tap ({x},{y})")
    adb(cfg, "shell", "input", "tap", str(x), str(y), check=False)
    time.sleep(wait)


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"  snap {dest.name} ({tag})")
    return dest


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=6)
    args = ap.parse_args()
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    snap(cfg, "s2-start")
    # dismiss popup if any (blank area)
    print("dismiss popup / blank")
    tap(cfg, 640, 360, wait=0.8)
    path = snap(cfg, "s2-after-dismiss")

    # 2nd icon peak y=266; try slightly left (icon body)
    print("click left #2 swords")
    tap(cfg, 155, 266, wait=1.5)
    path = snap(cfg, "s2-after-icon")
    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    print("btns", btns, "size", im.size)

    # If still looks like activity (5 similar rows + gold), try x=130 / y=266 again
    def gold(im0):
        n = 0
        for y in range(180, 320):
            for x in range(1050, 1200):
                r, g, b = im0.getpixel((x, y))
                if r > 170 and g > 130 and b < 110:
                    n += 1
        return n

    g = gold(im)
    print("gold_pixels", g)
    if g > 30:
        for xy in [(140, 266), (160, 266), (170, 266), (155, 270), (155, 260)]:
            print("retry", xy)
            tap(cfg, xy[0], xy[1], wait=1.4)
            path = snap(cfg, f"s2-retry-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            g = gold(im)
            btns = find_go_buttons(im)
            print("  gold", g, "btns", btns)
            if g <= 30:
                break

    # Maybe now on 战术挑战 / 素材页 — click 无音清剿 if present
    if len(btns) < 3:
        for xy in [(183, 531), (180, 500), (180, 560), (200, 480)]:
            print("try tacet sub", xy)
            tap(cfg, *xy, wait=1.3)
            path = snap(cfg, f"s2-tacet-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            print("  btns", btns)
            if len(btns) >= 3 and gold(im) <= 30:
                break

    print("FINAL btns", find_go_buttons(im), "gold", gold(im))
    print("last", path.name)
    # stop here for user/agent visual check — don't scroll until confirmed on list
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
