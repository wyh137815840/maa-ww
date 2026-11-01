#!/usr/bin/env python3
"""Fail if machine-local values leak into tracked files.

Checks every git-tracked text file for: the real PIN / serial / ref git host from
tools/touch-review/config.json (or env), full mainland phone numbers, and masked phones
(138****1234 style) other than the documented 138****1234 example.
Run before committing:  python tools/check_secrets.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import _local_cfg  # noqa: E402

SKIP_PREFIX = ("Android/MaaFwApp/",)
SKIP_SELF = {"tools/check_secrets.py", "tools/touch-review/config.example.json"}

literals = {
    "pin": _local_cfg.pin(),
    "serial": _local_cfg.serial(),
    "ref_git_base": _local_cfg.ref_git_base(),
}
EXAMPLE_PHONES = ("13800001234", "13900005678")  # documented placeholders
patterns = {
    "phone": re.compile(r"(?<![0-9])1[3-9][0-9]{9}(?![0-9])"),
    "masked phone": re.compile(r"(?<![0-9])(?!138\*{4}1234)[0-9]{3}\*{2,}[0-9]{4}"),
}


def main() -> int:
    files = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    ).stdout.split("\n")
    bad = 0
    for rel in files:
        if not rel or rel in SKIP_SELF or rel.startswith(SKIP_PREFIX):
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.split("\n"), 1):
            for name, lit in literals.items():
                if lit and lit in line:
                    print(f"{rel}:{n}: local {name} value")
                    bad += 1
            for name, rx in patterns.items():
                if rx.search(line) and not any(e in line for e in EXAMPLE_PHONES):
                    print(f"{rel}:{n}: {name}")
                    bad += 1
    print("OK: no leaks" if not bad else f"{bad} leak(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
