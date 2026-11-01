#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review/inbox"
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
base = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files"
for remote, local in [
    (f"{base}/log/run/run_20261101_005845_1.jsonl", OUT / "_run_fail.jsonl"),
    (f"{base}/log/app.log", OUT / "_app.log"),
]:
    subprocess.run(
        [c["adb_path"], "-s", c["serial"], "pull", remote, str(local)],
        capture_output=True,
        text=True,
    )
    print("pulled", local.name, local.stat().st_size if local.exists() else 0)

# tail maafw.log for PostBundle / error around 00:58
r = subprocess.run(
    [
        c["adb_path"],
        "-s",
        c["serial"],
        "shell",
        f"grep -nE 'PostBundle|资源加载|FAILED|error|Error|pipeline|Startup|StartApp|Invalidate|invalid' {base}/log/maafw.log | tail -80",
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
(OUT / "_maafw_grep.txt").write_text(r.stdout, encoding="utf-8")
print(r.stdout[-4000:] if r.stdout else r.stderr)
print("--- run ---")
print((OUT / "_run_fail.jsonl").read_text(encoding="utf-8", errors="ignore"))
print("--- app ---")
print((OUT / "_app.log").read_text(encoding="utf-8", errors="ignore")[-3000:])
