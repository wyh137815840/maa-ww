#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review/inbox"
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
remote = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/log/on_error/2026.11.01-01.43.18.102_TacetChallengeComplete.png"
local = OUT / "_on_error_challenge.png"
subprocess.run(
    [c["adb_path"], "-s", c["serial"], "pull", remote, str(local)],
    check=False,
)
print("pulled", local.exists(), local.stat().st_size if local.exists() else 0)
# also list recent on_error
r = subprocess.run(
    [
        c["adb_path"],
        "-s",
        c["serial"],
        "shell",
        "ls -t /storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/log/on_error | head -10",
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
