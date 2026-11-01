#!/usr/bin/env python3
"""Map 1280×720 pipeline coords ↔ device pixels (Odin 1920×1080 etc.)."""
from __future__ import annotations

import re
import subprocess

BASE_W, BASE_H = 1280, 720


def adb_run(adb: str, serial: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [adb, "-s", serial, *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def raw_screen_size(adb: str, serial: str) -> tuple[int, int]:
    """Prefer current app size (landscape game) over physical portrait panel."""
    # dumpsys: cur=1920x1080 app=1920x1080
    r = adb_run(adb, serial, "shell", "dumpsys", "window", "displays", check=False)
    m = re.search(r"cur=(\d+)x(\d+)", r.stdout or "")
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        if w >= h:
            return w, h
        return h, w  # force landscape pair if somehow swapped
    r2 = adb_run(adb, serial, "shell", "wm", "size", check=False)
    text = r2.stdout or ""
    # Override size: 1280x720 / Physical size: 1080x1920
    m2 = re.search(r"Override size:\s*(\d+)x(\d+)", text)
    if m2:
        return int(m2.group(1)), int(m2.group(2))
    m3 = re.search(r"Physical size:\s*(\d+)x(\d+)", text)
    if m3:
        w, h = int(m3.group(1)), int(m3.group(2))
        return (w, h) if w >= h else (h, w)
    return 1920, 1080


def to_device(x: int, y: int, device_w: int, device_h: int) -> tuple[int, int]:
    return int(round(x * device_w / BASE_W)), int(round(y * device_h / BASE_H))


def tap720(adb: str, serial: str, x720: int, y720: int, device_w: int, device_h: int) -> tuple[int, int]:
    dx, dy = to_device(x720, y720, device_w, device_h)
    adb_run(adb, serial, "shell", "input", "tap", str(dx), str(dy), check=False)
    return dx, dy


def swipe720(
    adb: str,
    serial: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    device_w: int,
    device_h: int,
    duration_ms: int = 400,
) -> tuple[tuple[int, int], tuple[int, int]]:
    a = to_device(x1, y1, device_w, device_h)
    b = to_device(x2, y2, device_w, device_h)
    adb_run(
        adb,
        serial,
        "shell",
        "input",
        "swipe",
        str(a[0]),
        str(a[1]),
        str(b[0]),
        str(b[1]),
        str(duration_ms),
        check=False,
    )
    return a, b
