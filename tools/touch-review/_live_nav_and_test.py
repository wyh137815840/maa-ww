#!/usr/bin/env python3
"""Continue from Terminal menu → 索拉指南 → 无音清剿 → SelectTacetRow proto test."""
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

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"


def adb(cfg, *args, check=True):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def tap(cfg, x, y, wait=1.0):
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
    ap.add_argument("--scroll-only", action="store_true")
    ap.add_argument("--from-terminal", action="store_true", help="already on ESC Terminal")
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    print(f"device={cfg['serial']}")

    path = snap(cfg, "nav-start")
    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    print("start buttons", btns)

    if len(btns) < 2:
        if args.from_terminal:
            # Terminal grid: 索拉指南 = row3 col1 on right panel
            # Empirically @1280x720 ~ (700, 500) — refine from snap if needed
            print("click 索拉指南 on Terminal")
            tap(cfg, 700, 505, wait=1.5)
            path = snap(cfg, "nav-after-guidebook-icon")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            print("after guidebook icon buttons", btns)

        if len(btns) < 2:
            # maybe still need open terminal first
            if not args.from_terminal:
                print("open Terminal via top-right menu ~ (1240, 40)")
                tap(cfg, 1240, 40, wait=1.2)
                path = snap(cfg, "nav-terminal")
                print("click 索拉指南")
                tap(cfg, 700, 505, wait=1.5)
                path = snap(cfg, "nav-after-guidebook-icon")
                im = Image.open(path).convert("RGB")
                btns = find_go_buttons(im)
                print("buttons", btns)

        if len(btns) < 2:
            print("click GuidebookTacetTab (183,531)")
            tap(cfg, 183, 531, wait=1.2)
            path = snap(cfg, "nav-after-tacet-tab")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            print("after tacet tab buttons", btns)

        if len(btns) < 2:
            # try alternate guidebook positions on terminal grid
            for xy in [(640, 500), (760, 500), (700, 470), (700, 540), (680, 510)]:
                print(f"retry 索拉指南 at {xy}")
                # ensure terminal: if not, might be wrong — reopen
                tap(cfg, xy[0], xy[1], wait=1.2)
                path = snap(cfg, f"nav-retry-{xy[0]}-{xy[1]}")
                im = Image.open(path).convert("RGB")
                btns = find_go_buttons(im)
                print("buttons", btns)
                if len(btns) >= 2:
                    break
                # if we opened something wrong, back
                adb(cfg, "shell", "input", "keyevent", "4", check=False)  # BACK
                time.sleep(0.8)

        if len(btns) < 2:
            print("click tacet tab again")
            tap(cfg, 183, 531, wait=1.2)
            path = snap(cfg, "nav-tacet-tab-final")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            print("final buttons", btns)

    if len(btns) < 2:
        raise SystemExit(f"still not on tacet list; last={path}")

    print(f"ON TACET LIST buttons={btns}")
    bar_top = detect_bar_top(im)
    p = plan(args.index, btns, bar_top)
    print("plan", p)
    if not p.get("ok"):
        raise SystemExit(p)

    if p["mode"] == "direct":
        if args.scroll_only:
            print("scroll-only: would click", p["click"])
            return 0
        cx, cy = p["click"]
        tap(cfg, cx, cy, wait=1.5)
        snap(cfg, f"after-click-idx{args.index}")
        return 0

    sx, sy = p["scrollbar_click"]
    print(f"scrollbar tap ({sx},{sy})")
    tap(cfg, sx, sy, wait=1.3)
    path2 = snap(cfg, f"after-scroll-idx{args.index}")
    im2 = Image.open(path2).convert("RGB")
    btns2 = find_go_buttons(im2)
    print("after scroll buttons", btns2)

    if btns2:
        max_y = max(b[1] for b in btns2)
        if max_y / 720 < 0.73 and "underscroll_retry_y" in p:
            ry = p["underscroll_retry_y"]
            print(f"underscroll nudge y={ry}")
            tap(cfg, sx, int(ry), wait=1.2)
            path2 = snap(cfg, f"after-nudge-idx{args.index}")
            im2 = Image.open(path2).convert("RGB")
            btns2 = find_go_buttons(im2)
            print("nudge buttons", btns2)

    if args.scroll_only:
        print("SCROLL-ONLY DONE")
        return 0

    if not btns2:
        raise SystemExit("no buttons after scroll")
    cx, cy = max(btns2, key=lambda b: b[1])
    print(f"click bottom btn ({cx},{cy})")
    tap(cfg, cx, cy, wait=1.5)
    snap(cfg, f"after-click-idx{args.index}")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
