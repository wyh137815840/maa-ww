#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
ww = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/pi"
end = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaend/files/pi"
cmd = f"""
echo '=== WW model tree ==='
find {ww}/resource/model -type f 2>/dev/null | sort
echo '=== END model tree ==='
find {end}/resource/model -type f 2>/dev/null | sort
echo '=== WW cfg ==='
ls -la {ww}/config 2>/dev/null; ls {ww}/config 2>/dev/null
find {ww} -name '*.json' -path '*/config/*' 2>/dev/null | head
echo '=== recent app files ==='
ls -la {ww}/ 2>/dev/null
"""
r = subprocess.run(
    [c["adb_path"], "-s", c["serial"], "shell", cmd],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
print(r.stderr)
