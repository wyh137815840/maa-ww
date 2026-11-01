#!/usr/bin/env python3
"""Capture MuMu player window client area via Win32 PrintWindow → 1280x720 inbox png."""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
from datetime import datetime
from pathlib import Path

from PIL import Image

from brief import write_brief
from common import load_config

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

PW_RENDERFULLCONTENT = 0x00000002


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def list_windows() -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []

    @EnumWindowsProc
    def _cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        if "MuMu" in title or "鸣潮" in title:
            found.append((int(hwnd), title))
        return True

    user32.EnumWindows(_cb, 0)
    return found


def capture_hwnd(hwnd: int) -> Image.Image:
    # Prefer client area (game surface without outer OS chrome if possible)
    rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetClientRect failed")
    left_top = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(left_top))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 1 or height <= 1:
        raise RuntimeError(f"bad client size {width}x{height}")

    hwnd_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bmp)
    ok = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
    if not ok:
        # fallback BitBlt from screen
        screen_dc = user32.GetDC(0)
        gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, left_top.x, left_top.y, 0x00CC0020)
        user32.ReleaseDC(0, screen_dc)

    # BITMAPINFO for 32bpp
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 3)]

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    buf_len = width * height * 4
    buf = (ctypes.c_ubyte * buf_len)()
    gdi32.GetDIBits(mem_dc, bmp, 0, height, ctypes.byref(buf), ctypes.byref(bmi), 0)

    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)

    img = Image.frombuffer("RGBA", (width, height), bytes(buf), "raw", "BGRA", 0, 1).convert("RGB")
    return img


def pick_hwnd(prefer: str) -> tuple[int, str]:
    wins = list_windows()
    if not wins:
        raise SystemExit("no MuMu window found")
    for hwnd, title in wins:
        if prefer and prefer in title:
            return hwnd, title
    # prefer device-1 / 鸣潮
    for hwnd, title in wins:
        if "设备-1" in title or "鸣潮" in title:
            return hwnd, title
    return wins[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="host-mumu")
    parser.add_argument("--prefer-title", default="设备-1")
    parser.add_argument("--brief-title", default="")
    parser.add_argument("--brief-goal", default="")
    parser.add_argument("--brief-label", default="")
    parser.add_argument("--brief-expected", default="")
    parser.add_argument("--step", action="append", default=[])
    args = parser.parse_args()

    cfg = load_config()
    hwnd, title = pick_hwnd(args.prefer_title)
    print("window", hex(hwnd), title)
    img = capture_hwnd(hwnd)
    tw, th = cfg["target_size"]
    if img.size != (tw, th):
        img = img.resize((tw, th), Image.Resampling.LANCZOS)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(cfg["inbox_dir"]) / f"{stamp}-{args.label}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    print(out)

    if args.brief_title and args.brief_goal:
        write_brief(
            out,
            title=args.brief_title,
            goal=args.brief_goal,
            steps=args.step or ["按说明框 ROI 并点点击点，然后导出。"],
            suggested_label=args.brief_label,
            suggested_expected_next=args.brief_expected,
            suggested_note=f"宿主窗口截取：{title}（因 ADB screencap 在安卓15鸣潮上会截到桌面）。",
            do_not=[],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
