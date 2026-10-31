#!/usr/bin/env python3
"""Write or update a task brief next to an inbox screenshot."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import load_config


def brief_path_for(image: Path) -> Path:
    return image.with_suffix(".brief.json")


def write_brief(
    image: Path,
    *,
    title: str,
    goal: str,
    steps: list[str],
    suggested_label: str = "",
    suggested_expected_next: str = "",
    suggested_note: str = "",
    do_not: list[str] | None = None,
) -> Path:
    payload = {
        "image": image.name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "goal": goal,
        "steps": steps,
        "suggested_label": suggested_label,
        "suggested_expected_next": suggested_expected_next,
        "suggested_note": suggested_note,
        "do_not": do_not or [],
    }
    out = brief_path_for(image)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    return out


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Attach a task brief to an inbox screenshot")
    parser.add_argument("image", help="inbox png name or path")
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--step", action="append", default=[], help="repeatable step text")
    parser.add_argument("--label", default="")
    parser.add_argument("--expected", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--do-not", action="append", default=[])
    args = parser.parse_args()

    image = Path(args.image)
    if not image.is_file():
        image = cfg["inbox_dir"] / Path(args.image).name
    if not image.is_file():
        raise SystemExit(f"image not found: {args.image}")

    out = write_brief(
        image,
        title=args.title,
        goal=args.goal,
        steps=args.step or ["按页面说明完成 ROI 与点击点标注，然后导出审查卡。"],
        suggested_label=args.label,
        suggested_expected_next=args.expected,
        suggested_note=args.note,
        do_not=args.do_not,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
