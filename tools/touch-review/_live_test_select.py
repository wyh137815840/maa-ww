#!/usr/bin/env python3
"""Odin live test: nav to 无音清剿, run SelectTacetRow proto (detect + scrollbar).

Uses 720p coords + device_geom.tap720 (device may be 1920×1080).
Does NOT click 开启挑战 — after 直接挑战, verifies team page then backs out.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402
from device_geom import raw_screen_size, swipe720, tap720  # noqa: E402
from tacet_select_proto import (  # noqa: E402
    BAR_TOP_FALLBACK,
    VIEWPORT_ROWS,
    detect_bar_top,
    detect_thumb,
    find_go_buttons,
    plan,
)

OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def load_nav() -> dict:
    if CALIB.exists():
        return json.loads(CALIB.read_text(encoding="utf-8")).get("coords_720p", {})
    return {
        "terminal_menu": [1198, 38],
        "sola_guidebook_tile": [634, 500],
        "tacet_tab_in_material": [183, 531],
    }


def snap(cfg: dict, label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"  snap {dest.name} ({tag})")
    return dest


def tap(cfg: dict, x: int, y: int, dw: int, dh: int, wait: float = 1.0) -> None:
    dx, dy = tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh)
    print(f"  tap720 ({x},{y}) -> ({dx},{dy})")
    time.sleep(wait)


def looks_like_tacet_list(im: Image.Image) -> bool:
    return len(find_go_buttons(im)) >= 2


def looks_like_team_page(im: Image.Image) -> bool:
    """Team prep: no list go-buttons + bright 开启挑战 pill bottom-right."""
    if looks_like_tacet_list(im):
        return False
    bright = 0
    for y in range(640, 690):
        for x in range(1020, 1180, 2):
            if sum(im.getpixel((x, y))) > 520:
                bright += 1
    return bright > 400


def open_tacet_list(cfg: dict, dw: int, dh: int) -> Path:
    nav = load_nav()
    path = snap(cfg, "live-start")
    im = Image.open(path).convert("RGB")
    if looks_like_tacet_list(im):
        print("already on tacet list")
        return path

    t = nav.get("terminal_menu", [1198, 38])
    print("tap Terminal", t)
    tap(cfg, t[0], t[1], dw, dh, wait=1.3)
    path = snap(cfg, "live-after-terminal")
    im = Image.open(path).convert("RGB")

    if not looks_like_tacet_list(im):
        s = nav.get("sola_guidebook_tile", [634, 500])
        print("tap 索拉指南", s)
        tap(cfg, s[0], s[1], dw, dh, wait=1.4)
        path = snap(cfg, "live-after-sola")
        im = Image.open(path).convert("RGB")

    if not looks_like_tacet_list(im):
        tab = nav.get("tacet_tab_in_material", [183, 531])
        print("tap 无音清剿", tab)
        tap(cfg, tab[0], tab[1], dw, dh, wait=1.2)
        path = snap(cfg, "live-after-tacet-tab")
        im = Image.open(path).convert("RGB")

    if not looks_like_tacet_list(im):
        raise SystemExit(f"failed to reach tacet list; see {path}")
    print(f"on tacet list, buttons={find_go_buttons(im)}")
    return path


def back_from_team(cfg: dict, dw: int, dh: int) -> None:
    # team page: top-right X is reliable; avoid Terminal/guidebook icons
    for xy in [(1235, 35), (40, 40), (60, 36)]:
        tap(cfg, xy[0], xy[1], dw, dh, wait=1.0)
        path = snap(cfg, f"live-back-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        if looks_like_tacet_list(im):
            print("back to tacet list")
            return
    print("WARN: may not be back on list")


def at_list_top(btns: list[tuple[int, int]]) -> bool:
    return len(btns) >= 3 and 220 <= btns[0][1] <= 260


def scroll_list_to_top(cfg: dict, dw: int, dh: int) -> None:
    """Drag scrollbar thumb to top until first-page button pitch."""
    for attempt in range(5):
        path0 = snap(cfg, f"live-before-scroll-top-{attempt}")
        im0 = Image.open(path0).convert("RGB")
        btns0 = find_go_buttons(im0)
        if at_list_top(btns0):
            print("already at list top", btns0)
            return
        thumb = detect_thumb(im0)
        if thumb:
            ya, yb, bx = thumb
            cy = (ya + yb) // 2
            print(f"  thumb ya={ya} yb={yb} x={bx} cy={cy}")
            a, b = swipe720(cfg["adb_path"], cfg["serial"], bx, cy, bx, 165, dw, dh, 550)
            print(f"  drag-bar {a}->{b}")
        else:
            print("  no thumb; tap track top")
            tap(cfg, 1245, 165, dw, dh, wait=0.4)
        time.sleep(0.55)
        path = snap(cfg, f"live-scroll-top-{attempt}")
        btns = find_go_buttons(Image.open(path).convert("RGB"))
        print("  buttons", btns)
        if at_list_top(btns):
            print("at list top")
            return
    print("WARN: may not be at top")


def run_select(cfg: dict, dw: int, dh: int, index: int, scroll_only: bool) -> dict:
    scroll_list_to_top(cfg, dw, dh)
    path = snap(cfg, f"live-before-idx{index}")
    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    bar_top = detect_bar_top(im, BAR_TOP_FALLBACK)
    p = plan(index, btns, bar_top)
    print(f"index={index} bar_top={bar_top:.4f} buttons={btns}")
    print(f"plan={p}")
    if not p.get("ok"):
        raise SystemExit(p)

    result = {"index": index, "plan": p, "ok": False}

    if p["mode"] == "direct":
        cx, cy = p["click"]
        if scroll_only:
            print(f"scroll-only: would click button ({cx},{cy})")
            result["ok"] = True
            return result
        print(f"tap button ({cx},{cy})")
        tap(cfg, cx, cy, dw, dh, wait=1.6)
        path2 = snap(cfg, f"live-after-click-idx{index}")
        im2 = Image.open(path2).convert("RGB")
        title = path2.with_name(path2.stem + "-title.png")
        im2.crop((20, 20, 520, 110)).save(title)
        ok = looks_like_team_page(im2)
        result["ok"] = ok
        result["file"] = path2.name
        result["title"] = title.name
        print("reached_team_page" if ok else "FAIL: still on list?")
        if ok:
            back_from_team(cfg, dw, dh)
        return result

    # Odin: scrollbar tap often no-ops. Empirically one 100px content swipe ≈ 2 rows.
    rows = max(0, index - VIEWPORT_ROWS)
    # target at bottom ⇒ scroll `rows` items; dy≈50px per row @720p
    dy = max(50, rows * 50)
    y0, y1 = 520, max(200, 520 - dy)
    print(f"content-swipe rows≈{rows} dy={dy} (520→{y1}) index={index}")
    swipe720(cfg["adb_path"], cfg["serial"], 820, y0, 820, y1, dw, dh, min(700, 300 + dy))
    time.sleep(0.7)
    path2 = snap(cfg, f"live-after-scroll-idx{index}")
    im2 = Image.open(path2).convert("RGB")
    btns2 = find_go_buttons(im2)
    print(f"after scroll buttons={btns2}")
    # if underscrolled (still looks like top), nudge once
    if btns2 and btns2[0][1] <= 260 and rows >= 2:
        print("underscroll nudge +1 row")
        swipe720(cfg["adb_path"], cfg["serial"], 820, 500, 820, 450, dw, dh, 350)
        time.sleep(0.55)
        path2 = snap(cfg, f"live-after-nudge-idx{index}")
        im2 = Image.open(path2).convert("RGB")
        btns2 = find_go_buttons(im2)
        print(f"nudge buttons={btns2}")

    if scroll_only:
        result["ok"] = len(btns2) >= 1 and btns2 != btns
        result["buttons_after"] = btns2
        print("scroll-only: stop before clicking 直接挑战")
        return result

    if not btns2:
        raise SystemExit("no go buttons after scroll")

    cx, cy = max(btns2, key=lambda b: b[1])
    print(f"tap bottom button ({cx},{cy})")
    tap(cfg, cx, cy, dw, dh, wait=1.6)
    path3 = snap(cfg, f"live-after-click-idx{index}")
    im3 = Image.open(path3).convert("RGB")
    title = path3.with_name(path3.stem + "-title.png")
    im3.crop((20, 20, 520, 110)).save(title)
    ok = looks_like_team_page(im3)
    result["ok"] = ok
    result["file"] = path3.name
    result["title"] = title.name
    result["buttons_after_scroll"] = btns2
    print("reached_team_page" if ok else "FAIL: still on list?")
    if ok:
        back_from_team(cfg, dw, dh)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=6, help="1-based tacet index")
    ap.add_argument("--indices", type=str, default="", help="comma list e.g. 1,6,12")
    ap.add_argument("--scroll-only", action="store_true")
    ap.add_argument("--skip-nav", action="store_true")
    args = ap.parse_args()

    indices = [int(x) for x in args.indices.split(",") if x.strip()] if args.indices else [args.index]

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"device={cfg['serial']} raw={dw}x{dh}")

    if not args.skip_nav:
        open_tacet_list(cfg, dw, dh)
    else:
        snap(cfg, "live-skip-nav")

    results = []
    for idx in indices:
        print(f"\n=== select index {idx} ===")
        results.append(run_select(cfg, dw, dh, idx, args.scroll_only))

    print("\nSUMMARY", json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r.get("ok") for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
