#!/usr/bin/env python3
"""From 素材获取 sidebar, click 无音清剿 (6th icon) and save final calib."""
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
from tacet_select_proto import find_go_buttons

ROOT = Path(__file__).resolve().parents[2]
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"
OUT = ROOT / "review/inbox"


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])

    def tap(x, y, wait=1.2):
        print(" tap", (x, y), "->", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
        time.sleep(wait)

    # 素材获取 left rail ~7 icons; 无音清剿 is 6th (pipeline 183,531)
    for xy in [(183, 531), (180, 540), (180, 560), (170, 520)]:
        tap(*xy)
        path = snap(cfg, f"odin-tacetrail-{xy[0]}-{xy[1]}")
        btns = find_go_buttons(Image.open(path).convert("RGB"))
        print(" btns", btns)
        if len(btns) >= 3:
            out = {
                "device_raw": [dw, dh],
                "serial": cfg["serial"],
                "coords_720p": {
                    "terminal_menu": [1198, 38],
                    "sola_guidebook_tile": [634, 500],
                    "tacet_tab_in_material": list(xy),
                    "notes": {
                        "980_40": "唤取(错误)",
                        "rail_2nd_in_material": "凝素/模拟，不是无音清剿",
                        "tacet": "素材获取左侧第6项≈(183,531)",
                    },
                },
                "nav_path": [
                    "大世界 → Terminal(1198,38)",
                    "→ 索拉指南(634,500) 进入素材获取/指南",
                    "→ 无音清剿 tab",
                    "→ SelectTacetRow",
                ],
                "final": {"file": path.name, "buttons": btns, "ok": True},
            }
            CALIB.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0

    print("FAILED")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
