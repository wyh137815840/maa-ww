#!/usr/bin/env python3
"""Cross-compile MaaWW go-service for Android into MaaFwApp agent-dist.

Output:

    Android/agent-dist/<abi>/jniLibs/libgo-service.so

Requires Go + Android NDK (ANDROID_NDK_ROOT / ANDROID_HOME/ndk/*).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ABI = "arm64-v8a"
DEFAULT_API = 23
GOARCH_BY_ABI = {"arm64-v8a": "arm64", "x86_64": "amd64"}
CLANG_TRIPLE_BY_ABI = {
    "arm64-v8a": "aarch64-linux-android",
    "x86_64": "x86_64-linux-android",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"[ERR] {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    log(f"[RUN] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=cwd, env=env)
    if completed.returncode != 0:
        die(f"command failed ({completed.returncode}): {' '.join(cmd)}")


def host_ndk_prebuilt() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return "windows-x86_64"
    if system == "darwin":
        return "darwin-arm64" if machine in {"arm64", "aarch64"} else "darwin-x86_64"
    return "linux-x86_64"


def find_ndk(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    for key in ("ANDROID_NDK_ROOT", "ANDROID_NDK_HOME", "NDK_ROOT"):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]))
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        # MaaWW local android-build layout
        local = Path(r"D:\git\视频学习\tools\android-build\sdk")
        if local.is_dir():
            sdk = str(local)
    if sdk:
        ndk_root = Path(sdk) / "ndk"
        if ndk_root.is_dir():
            versions = sorted(
                (p for p in ndk_root.iterdir() if p.is_dir() and (p / "source.properties").exists()),
                key=lambda p: p.name,
                reverse=True,
            )
            candidates.extend(versions)
    for c in candidates:
        if c.is_dir() and (c / "source.properties").exists():
            return c.resolve()
    die("Android NDK not found; set ANDROID_NDK_ROOT or install under ANDROID_HOME/ndk")


def build_go(*, ndk: Path, abi: str, api: int, version: str, out_so: Path) -> None:
    go = shutil.which("go")
    if not go:
        # Fresh winget install may not be on PATH yet
        candidate = Path(r"C:\Program Files\Go\bin\go.exe")
        if candidate.is_file():
            go = str(candidate)
        else:
            die("go not found on PATH")
    prebuilt = ndk / "toolchains" / "llvm" / "prebuilt" / host_ndk_prebuilt() / "bin"
    clang = prebuilt / ("clang.exe" if os.name == "nt" else "clang")
    clangxx = prebuilt / ("clang++.exe" if os.name == "nt" else "clang++")
    if not clang.is_file():
        die(f"NDK clang not found: {clang}")
    triple = f"{CLANG_TRIPLE_BY_ABI[abi]}{api}"
    target = f"--target={triple}"
    env = os.environ.copy()
    # Prefer CN proxy when unset (common on mainland networks).
    env.setdefault("GOPROXY", "https://goproxy.cn,direct")
    env.setdefault("GOSUMDB", "sum.golang.google.cn")
    # Avoid sandboxed / locked %TEMP% on some Windows agents.
    gotmp = Path(env.get("GOTMPDIR") or env.get("TEMP") or ROOT / "tools" / "_gotmp")
    gotmp.mkdir(parents=True, exist_ok=True)
    env["GOTMPDIR"] = str(gotmp)
    env["TMP"] = str(gotmp)
    env["TEMP"] = str(gotmp)
    env.update(
        {
            "GOOS": "android",
            "GOARCH": GOARCH_BY_ABI[abi],
            "CGO_ENABLED": "1",
            "CC": str(clang),
            "CXX": str(clangxx),
            "CGO_CFLAGS": target,
            "CGO_CXXFLAGS": target,
            "CGO_LDFLAGS": target,
            "GOTOOLCHAIN": env.get("GOTOOLCHAIN", "auto"),
        }
    )
    out_so.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        go,
        "build",
        "-trimpath",
        "-buildvcs=false",
        f"-ldflags=-X main.Version={version}",
        "-o",
        str(out_so),
        ".",
    ]
    run(cmd, cwd=ROOT / "agent" / "go-service", env=env)
    log(f"[OK] {out_so} ({out_so.stat().st_size} bytes)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ndk", default=None, help="Android NDK root")
    p.add_argument(
        "--abi",
        action="append",
        choices=sorted(GOARCH_BY_ABI),
        help=f"target ABI (default {DEFAULT_ABI})",
    )
    p.add_argument("--api", type=int, default=DEFAULT_API)
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "Android" / "agent-dist",
        help="agent.sourceDir (default Android/agent-dist)",
    )
    p.add_argument("--version", default=os.environ.get("MAAWW_VERSION", "dev"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ndk = find_ndk(args.ndk)
    os.environ["ANDROID_NDK_ROOT"] = str(ndk)
    log(f"[NDK] {ndk}")

    for abi in dict.fromkeys(args.abi or [DEFAULT_ABI]):
        log(f"[ABI] {abi}")
        out_so = args.out.resolve() / abi / "jniLibs" / "libgo-service.so"
        build_go(ndk=ndk, abi=abi, api=args.api, version=args.version, out_so=out_so)
        log(f"[DONE] {out_so}")


if __name__ == "__main__":
    main()
