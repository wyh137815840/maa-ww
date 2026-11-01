#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ADB = r"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe"
SERIAL = "127.0.0.1:16416"
OUT = Path(__file__).resolve().parents[2] / "review" / "inbox"
MUMU_CLI = Path(r"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\mumu-cli.exe")


def run(args, timeout=60):
    return subprocess.run(args, capture_output=True, timeout=timeout)


def sh(cmd, timeout=60):
    return run([ADB, "-s", SERIAL, "shell", cmd], timeout=timeout)


def save(name: str, local: Path) -> None:
    out = OUT / name
    out.write_bytes(local.read_bytes())
    im = Image.open(out).convert("RGB")
    c = im.getpixel((im.size[0] // 2, im.size[1] // 2))
    # variance proxy: sample a few points
    pts = [im.getpixel((x, y)) for x, y in [(100, 100), (640, 360), (1100, 600), (200, 500)]]
    print(name, im.size, "center", c, "samples", pts)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    run([ADB, "connect", SERIAL])

    # parse unique display ids from SurfaceFlinger display dump
    sf = sh("dumpsys SurfaceFlinger --display-id").stdout.decode("utf-8", "ignore")
    print("SF --display-id:\n", sf[:800])
    ids = re.findall(r"(?:Display\s+)?(\d{10,})", sf)
    # also from dumpsys display uniqueId local:NUMBER
    disp = sh("dumpsys display").stdout.decode("utf-8", "ignore")
    ids += re.findall(r'uniqueId="local:(\d+)"', disp)
    # name mapping
    named = re.findall(r'DisplayDeviceInfo\{"([^"]+)".*?uniqueId="local:(\d+)"', disp, flags=re.S)
    print("named displays:", named)
    ids = list(dict.fromkeys(ids))
    print("candidate ids:", ids)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # capture all
        remote_base = "/data/local/tmp/cap_all.png"
        sh("rm -f /data/local/tmp/cap_all*.png")
        r = sh(f"screencap -a -p {remote_base}")
        print("screencap -a", r.returncode, r.stderr.decode("utf-8", "ignore")[:200])
        # list remote
        ls = sh("ls -l /data/local/tmp/cap_all*.png").stdout.decode("utf-8", "ignore")
        print(ls)
        for line in ls.splitlines():
            m = re.search(r"(cap_all.*\.png)$", line.strip())
            if not m:
                continue
            remote = f"/data/local/tmp/{m.group(1)}"
            local = tmp_p / m.group(1)
            run([ADB, "-s", SERIAL, "pull", remote, str(local)])
            if local.exists():
                save(f"_all-{m.group(1)}", local)

        for did in ids:
            remote = f"/data/local/tmp/cap_{did}.png"
            sh(f"rm -f {remote}")
            r = sh(f"screencap -d {did} -p {remote}")
            err = r.stderr.decode("utf-8", "ignore")
            print(f"screencap -d {did} rc={r.returncode} {err[:120]!r}")
            local = tmp_p / f"{did}.png"
            run([ADB, "-s", SERIAL, "pull", remote, str(local)])
            if local.exists() and local.stat().st_size > 1000:
                # map name if possible
                label = did
                for n, i in named:
                    if i == did:
                        label = n
                        break
                save(f"_disp-{label}.png", local)

    # mumu-cli help
    if MUMU_CLI.is_file():
        h = run([str(MUMU_CLI), "--help"])
        text = (h.stdout + h.stderr).decode("utf-8", "ignore")
        print("mumu-cli help head:\n", text[:1000])
        for sub in ("help", "screenshot", "capture", "player", "control"):
            h2 = run([str(MUMU_CLI), sub, "--help"])
            t2 = (h2.stdout + h2.stderr).decode("utf-8", "ignore")
            if t2.strip():
                print(f"mumu-cli {sub}:\n", t2[:500])


if __name__ == "__main__":
    main()
