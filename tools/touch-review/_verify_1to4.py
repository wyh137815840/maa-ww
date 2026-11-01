#!/usr/bin/env python3
"""Acceptance: indices 1–4 (first page, direct click → team page → back)."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons, plan

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def snap(cfg, label: str) -> Path:
    dest = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def tap(cfg, x, y, dw, dh, wait=1.0):
    print("  tap720", (x, y), "->", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(wait)


def looks_team(im: Image.Image) -> bool:
    """编队页：列表无「直接挑战」+ 右下「开启挑战」亮块。"""
    if len(find_go_buttons(im)) >= 2:
        return False
    bright = sum(
        1
        for y in range(640, 690)
        for x in range(1020, 1180, 2)
        if sum(im.getpixel((x, y))) > 520
    )
    return bright > 400


def reopen(cfg, dw, dh) -> None:
    nav = json.loads(CALIB.read_text(encoding="utf-8"))["coords_720p"]
    for _ in range(3):
        tap(cfg, 1235, 35, dw, dh, 0.8)
    time.sleep(0.8)
    tap(cfg, *nav["terminal_menu"], dw, dh, 1.6)
    tap(cfg, *nav["sola_guidebook_tile"], dw, dh, 1.5)
    tap(cfg, *nav["tacet_tab_in_material"], dw, dh, 1.3)
    path = snap(cfg, "acc-reopen")
    btns = find_go_buttons(Image.open(path).convert("RGB"))
    print("reopen buttons", btns)
    if len(btns) < 4:
        raise SystemExit(f"not on first-page tacet list: {btns}")


def back(cfg, dw, dh) -> bool:
    for xy in [(1235, 35), (40, 40)]:
        tap(cfg, *xy, dw, dh, 1.0)
        im = Image.open(snap(cfg, f"acc-back-{xy[0]}")).convert("RGB")
        if len(find_go_buttons(im)) >= 2:
            print("back to list")
            return True
    return False


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"device={cfg['serial']} raw={dw}x{dh}")

    path = snap(cfg, "acc-start")
    btns = find_go_buttons(Image.open(path).convert("RGB"))
    if len(btns) < 4 or btns[0][1] > 260:
        print("need reopen")
        reopen(cfg, dw, dh)

    results = []
    for index in (1, 2, 3, 4):
        print(f"\n=== index {index} ===")
        # ensure top
        path = snap(cfg, f"acc-before-{index}")
        im = Image.open(path).convert("RGB")
        btns = find_go_buttons(im)
        if len(btns) < 4 or btns[0][1] > 260:
            reopen(cfg, dw, dh)
            path = snap(cfg, f"acc-before-{index}-2")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
        p = plan(index, btns)
        print("plan", p)
        if not p.get("ok") or p.get("mode") != "direct":
            results.append({"index": index, "ok": False, "reason": "not direct/first-page"})
            continue
        cx, cy = p["click"]
        tap(cfg, cx, cy, dw, dh, 1.6)
        after = snap(cfg, f"acc-after-{index}")
        ok = looks_team(Image.open(after).convert("RGB"))
        print("team" if ok else "FAIL", after.name)
        results.append({"index": index, "ok": ok, "click": [cx, cy], "file": after.name})
        if ok:
            if not back(cfg, dw, dh):
                reopen(cfg, dw, dh)
        else:
            reopen(cfg, dw, dh)

    print("\nACCEPTANCE", json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r["ok"] for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
