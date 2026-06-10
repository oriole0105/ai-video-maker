#!/usr/bin/env python3
"""prepare_offline.py — 預先下載 Windows 所需套件與模型（在家有網路時執行）

執行完畢後，將整個 ai-video-maker/ 資料夾（含 offline_pack/）複製給同仁，
同仁在 Windows 上雙擊 setup_offline.bat 即可完成安裝。

用法：
  python prepare_offline.py              # 下載套件 + 模型（預設 Python 3.10）
  python prepare_offline.py --py 311     # 指定 Python 3.11
  python prepare_offline.py --wheels-only
  python prepare_offline.py --model-only
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
OFFLINE_DIR = SCRIPT_DIR / "offline_pack"
WHEELS_DIR = OFFLINE_DIR / "wheels"
MODEL_DIR = OFFLINE_DIR / "whisper_model"
PIPER_MODEL_DIR = OFFLINE_DIR / "piper_model"

WIN_PACKAGES = ["edge-tts", "faster-whisper", "opencc-python-reimplemented", "piper-tts"]
HF_REPO = "Systran/faster-whisper-medium"

PIPER_MODEL_NAME = "zh_CN-huayan-medium"
PIPER_HF_BASE = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    "/zh/zh_CN/huayan/medium"
)


# ── 下載輔助 ──────────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path) -> None:
    if dest.exists():
        size_mb = dest.stat().st_size // (1024 * 1024)
        print(f"  略過（已存在 {size_mb} MB）：{dest.name}")
        return

    req = urllib.request.Request(url, headers={"User-Agent": "prepare_offline/1.0"})
    try:
        with urllib.request.urlopen(req) as r:
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                while chunk := r.read(1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        mb = downloaded // (1024 * 1024)
                        print(f"\r  {dest.name}  {pct:3d}%  ({mb} MB / {total // (1024*1024)} MB)",
                              end="", flush=True)
        mb = downloaded // (1024 * 1024)
        print(f"\r  ✅ {dest.name:<40} {mb} MB")
    except Exception as e:
        dest.unlink(missing_ok=True)
        print(f"\n  ❌ 下載失敗：{dest.name}  {e}", flush=True)
        raise


def hf_file_list(repo: str) -> list[str]:
    url = f"https://huggingface.co/api/models/{repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "prepare_offline/1.0"})
    with urllib.request.urlopen(req) as r:
        info = json.loads(r.read())
    return [s["rfilename"] for s in info.get("siblings", [])
            if not s["rfilename"].startswith(".")]


# ── 步驟 ──────────────────────────────────────────────────────────────────────

def step_piper_model() -> None:
    print(f"\n[ 2/3 ] 下載 Piper 語音模型（{PIPER_MODEL_NAME}，約 80 MB）...")
    PIPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for ext in (".onnx", ".onnx.json"):
        fname = PIPER_MODEL_NAME + ext
        download_file(f"{PIPER_HF_BASE}/{fname}", PIPER_MODEL_DIR / fname)
    print(f"  ✅ Piper 模型下載完成 → {PIPER_MODEL_DIR}")


def step_wheels(py_ver: str) -> None:
    print(f"\n[ 1/3 ] 下載 Windows 套件 (Python {py_ver}, win_amd64)...")
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "pip", "download",
        *WIN_PACKAGES,
        "--dest", str(WHEELS_DIR),
        "--platform", "win_amd64",
        "--python-version", py_ver,
        "--implementation", "cp",
        "--abi", f"cp{py_ver}",
        "--only-binary", ":all:",
    ]
    print(f"  套件：{', '.join(WIN_PACKAGES)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print()
        print("  ❌ 下載失敗。可能原因：")
        print(f"     ctranslate2 沒有 Python {py_ver} 的預編譯 wheel")
        print(f"     解法：試試 --py 310 或 --py 311")
        sys.exit(1)

    count = len(list(WHEELS_DIR.glob("*.whl")))
    print(f"  ✅ 完成，共 {count} 個 wheel 檔案")


def step_model() -> None:
    print(f"\n[ 3/3 ] 下載 Whisper 模型（{HF_REPO}）...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("  取得檔案清單...", end="", flush=True)
    try:
        files = hf_file_list(HF_REPO)
    except Exception as e:
        print(f"\n  ❌ 無法取得檔案清單：{e}")
        sys.exit(1)
    print(f"\r  共 {len(files)} 個檔案")

    base = f"https://huggingface.co/{HF_REPO}/resolve/main"
    for fname in files:
        download_file(f"{base}/{fname}", MODEL_DIR / fname)

    total_mb = sum(f.stat().st_size for f in MODEL_DIR.rglob("*") if f.is_file()) // (1024 * 1024)
    print(f"  ✅ 模型下載完成（共 {total_mb} MB）→ {MODEL_DIR}")


# ── 結果摘要 ──────────────────────────────────────────────────────────────────

def print_summary(py_ver: str) -> None:
    wheels_n = len(list(WHEELS_DIR.glob("*.whl"))) if WHEELS_DIR.exists() else 0
    whisper_mb = sum(f.stat().st_size for f in MODEL_DIR.rglob("*") if f.is_file()) // (1024 * 1024) \
                 if MODEL_DIR.exists() else 0
    piper_mb = sum(f.stat().st_size for f in PIPER_MODEL_DIR.rglob("*") if f.is_file()) // (1024 * 1024) \
               if PIPER_MODEL_DIR.exists() else 0

    print()
    print("=" * 56)
    print("  offline_pack/ 準備完成")
    print("=" * 56)
    print(f"  wheels/          {wheels_n} 個 wheel，Python {py_ver} / win_amd64")
    print(f"  whisper_model/   {whisper_mb} MB")
    print(f"  piper_model/     {piper_mb} MB")
    print()
    print("  傳給同仁的步驟：")
    print("  1. 將整個 ai-video-maker/ 壓縮後傳給同仁")
    print("     （含 offline_pack/，約 2 GB）")
    print("  2. 同仁解壓後雙擊執行 setup_offline.bat")
    print()
    print("  ℹ️  TTS 模式比較：")
    print("     --tts edge   需連到 *.tts.speech.microsoft.com（台灣腔，最自然）")
    print("     --tts piper  完全離線（普通話腔，CPU 極快）")
    print("     --tts melo   僅線上安裝，不含於此離線包（CPU 中速）")
    print("=" * 56)


def main() -> None:
    p = argparse.ArgumentParser(description="預先下載 Windows 離線安裝包")
    p.add_argument("--py", default="310", metavar="VER",
                   help="目標 Python 版本，不含小數點（預設：310）")
    p.add_argument("--wheels-only",  action="store_true", help="只下載套件")
    p.add_argument("--model-only",   action="store_true", help="只下載 Whisper 模型")
    p.add_argument("--piper-only",   action="store_true", help="只下載 Piper 模型")
    args = p.parse_args()

    print("=== prepare_offline.py ===")
    print(f"輸出目錄：{OFFLINE_DIR}")

    only = args.wheels_only or args.model_only or args.piper_only
    if not args.model_only and not args.piper_only:
        step_wheels(args.py)
    if not args.wheels_only and not args.piper_only:
        step_model()
    if not args.wheels_only and not args.model_only:
        step_piper_model()

    print_summary(args.py)


if __name__ == "__main__":
    main()
