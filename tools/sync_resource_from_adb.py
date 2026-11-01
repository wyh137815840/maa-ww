#!/usr/bin/env python3
"""Sync resource_adb pipeline/image into Official ./resource for single-bundle Android load.

Why: MaaFramework PostBundle each path independently; our attach of resource_adb was failing
on-device while ./resource (with OCR model) loads. Phase-1 Official path is only ./resource.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/resource_adb"
DST = ROOT / "assets/resource"


def main() -> int:
    if not SRC.is_dir():
        print("missing", SRC, file=sys.stderr)
        return 2
    DST.mkdir(parents=True, exist_ok=True)

    # pipelines
    dp = DST / "pipeline"
    if dp.exists():
        shutil.rmtree(dp)
    shutil.copytree(SRC / "pipeline", dp)
    print("pipeline", len(list(dp.glob("*.json"))), "files")

    # images
    di = DST / "image"
    if di.exists():
        shutil.rmtree(di)
    if (SRC / "image").is_dir():
        shutil.copytree(
            SRC / "image",
            di,
            ignore=shutil.ignore_patterns(".gitkeep"),
        )
        print("image", len(list(di.rglob("*.png"))), "png")

    # default_pipeline: keep resource one; do not overwrite with adb if missing
    if not (DST / "default_pipeline.json").exists() and (SRC / "default_pipeline.json").exists():
        shutil.copy2(SRC / "default_pipeline.json", DST / "default_pipeline.json")

    onnx = DST / "model" / "ocr" / "rec.onnx"
    if not onnx.is_file():
        print(
            "WARN: assets/resource/model/ocr/rec.onnx missing — add MaaEnd-AI submodule "
            "or copy from device MaaEnd. PostBundle will fail without OCR model.",
            file=sys.stderr,
        )
        return 1
    print("ok model", onnx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
