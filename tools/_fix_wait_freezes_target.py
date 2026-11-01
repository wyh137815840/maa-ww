#!/usr/bin/env python3
"""Rewrite mistaken wait_freezes target:0.95 → threshold:0.95 in pipeline JSONs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "assets/resource_adb/pipeline/Tacet.json",
    ROOT / "assets/resource_adb/pipeline/CommonDisconnect.json",
    ROOT / "assets/resource/pipeline/Tacet.json",
    ROOT / "assets/resource/pipeline/CommonDisconnect.json",
]


def fix_obj(obj):
    changed = 0
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in ("pre_wait_freezes", "post_wait_freezes", "repeat_wait_freezes") and isinstance(v, dict):
                if v.get("target") == 0.95:
                    del v["target"]
                    v["threshold"] = 0.95
                    changed += 1
            else:
                changed += fix_obj(v)
    elif isinstance(obj, list):
        for x in obj:
            changed += fix_obj(x)
    return changed


def main() -> int:
    total = 0
    for p in PATHS:
        if not p.is_file():
            print("skip missing", p)
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        n = fix_obj(data)
        if n:
            p.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(p.relative_to(ROOT), "fixed", n)
        total += n
    print("total", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
