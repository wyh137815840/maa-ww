#!/usr/bin/env python3
"""Probe ways to capture the game framebuffer via ADB on MuMu A15."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ADB = r"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe"
SERIAL = "127.0.0.1:16416"
OUT = Path(__file__).resolve().parents[2] / "review" / "inbox"


def run(args: list[str], timeout: int = 40) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, capture_output=True, timeout=timeout)


def sh(cmd: str, timeout: int = 40) -> subprocess.CompletedProcess[bytes]:
    return run([ADB, "-s", SERIAL, "shell", cmd], timeout=timeout)


def save_img(name: str, path_or_bytes) -> None:
    out = OUT / name
    if isinstance(path_or_bytes, (bytes, bytearray)):
        out.write_bytes(path_or_bytes)
        src = out
    else:
        src = Path(path_or_bytes)
        if src != out:
            out.write_bytes(src.read_bytes())
    try:
        im = Image.open(out).convert("RGB")
        c = im.getpixel((im.size[0] // 2, im.size[1] // 2))
        # classify: desktop wallpaper tends to dark blue; game UI brighter/varied
        print(f"{name}: size={im.size} center={c}")
    except Exception as exc:
        print(f"{name}: FAIL {exc} bytes={out.stat().st_size if out.exists() else 0}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    run([ADB, "connect", SERIAL])

    print("=== focus / pid ===")
    print(sh("pidof com.kurogame.mingchao").stdout.decode("utf-8", "ignore").strip())
    act = sh("dumpsys activity activities").stdout.decode("utf-8", "ignore")
    for line in act.splitlines():
        if "topResumedActivity" in line or "mResumedActivity" in line:
            print(line.strip()[:200])
            break

    print("=== displays ===")
    disp = sh("dumpsys display").stdout.decode("utf-8", "ignore")
    ids = sorted(set(re.findall(r"mDisplayId=(\d+)", disp)))
    print("mDisplayId", ids)
    for line in disp.splitlines():
        if "DisplayDeviceInfo" in line or "uniqueId" in line[:40] or "mCurrentLayerStack" in line:
            print(line.strip()[:180])

    # SurfaceFlinger displays
    sf = sh("service call SurfaceFlinger 1013").stdout  # sometimes list
    print("sf1013", sf[:120])

    # Try screencap per display id if supported
    help_out = sh("screencap -h").stderr + sh("screencap -h").stdout
    print("screencap help:", help_out.decode("utf-8", "ignore")[:400])

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        # default
        remote = "/data/local/tmp/cap_default.png"
        sh(f"rm -f {remote}")
        sh(f"screencap -p {remote}")
        local = tmp_p / "default.png"
        run([ADB, "-s", SERIAL, "pull", remote, str(local)])
        if local.exists():
            save_img("_probe-default.png", local)

        for did in ids or ["0", "1"]:
            remote = f"/data/local/tmp/cap_d{did}.png"
            sh(f"rm -f {remote}")
            # Android 14+ may support -d
            r = sh(f"screencap -d {did} -p {remote}")
            print(f"screencap -d {did} rc={r.returncode} err={r.stderr[:120]!r}")
            local = tmp_p / f"d{did}.png"
            run([ADB, "-s", SERIAL, "pull", remote, str(local)])
            if local.exists() and local.stat().st_size > 1000:
                save_img(f"_probe-d{did}.png", local)

        # cmd screenshot (some devices)
        remote = "/data/local/tmp/cap_cmd.png"
        sh(f"rm -f {remote}")
        r = sh(f"cmd statusbar 2>/dev/null; screencap {remote}")
        # raw rgba screencap without -p
        remote_raw = "/data/local/tmp/cap.raw"
        sh(f"rm -f {remote_raw}")
        sh(f"screencap {remote_raw}")
        local_raw = tmp_p / "cap.raw"
        run([ADB, "-s", SERIAL, "pull", remote_raw, str(local_raw)])
        if local_raw.exists() and local_raw.stat().st_size > 1000:
            data = local_raw.read_bytes()
            # header: width,height,format as uint32 LE
            if len(data) >= 12:
                import struct

                w, h, fmt = struct.unpack_from("<III", data, 0)
                print(f"raw header w={w} h={h} fmt={fmt} nbytes={len(data)}")
                payload = data[12:]
                try:
                    if fmt == 1 and len(payload) >= w * h * 4:  # RGBA_8888
                        im = Image.frombuffer("RGBA", (w, h), payload[: w * h * 4], "raw", "RGBA", 0, 1).convert("RGB")
                        im.save(OUT / "_probe-rawrgba.png")
                        save_img("_probe-rawrgba.png", OUT / "_probe-rawrgba.png")
                except Exception as exc:
                    print("raw decode fail", exc)

    # layer dumpsys briefly for GameActivity / SurfaceView
    layers = sh("dumpsys SurfaceFlinger --list").stdout.decode("utf-8", "ignore")
    for key in ("mingchao", "GameActivity", "SurfaceView", "BLAST", "Wallpaper", "lawnchair"):
        hits = [ln for ln in layers.splitlines() if key.lower() in ln.lower()]
        print(f"layers~{key}: {len(hits)}")
        for ln in hits[:5]:
            print(" ", ln[:160])

    # MuMu / nemu screenshot binaries?
    ls = sh("ls /system/bin /system/xbin /vendor/bin 2>/dev/null").stdout.decode("utf-8", "ignore")
    for token in ls.split():
        t = token.lower()
        if any(k in t for k in ("screen", "capt", "nemu", "mumu", "shot")):
            print("bin", token)


if __name__ == "__main__":
    main()
