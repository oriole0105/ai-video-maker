#!/usr/bin/env python3
"""setup.py — ai-video-maker 環境安裝腳本

用法：
  python setup.py          # 安裝所有 Python 套件
  python setup.py --check  # 只檢查環境，不安裝

系統工具（需手動安裝，腳本會提示）：
  Mac：
    brew install ffmpeg
    npm install -g @marp-team/marp-cli
    brew install --cask google-chrome
  Windows（需先安裝 winget / Node.js）：
    winget install ffmpeg
    npm install -g @marp-team/marp-cli
    winget install Google.Chrome
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_DIR = SCRIPT_DIR / "venv"


# ── 平台輔助 ──────────────────────────────────────────────────────────────────

def is_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"


def venv_python(name: str) -> Path:
    base = VENV_DIR / name
    if sys.platform == "win32":
        return base / "Scripts" / "python.exe"
    return base / "bin" / "python"


def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=False, text=True)


def uv_create_venv(name: str) -> None:
    path = VENV_DIR / name
    subprocess.run(["uv", "venv", str(path), "--clear"], check=True,
                   capture_output=True)


def uv_install(venv_name: str, *packages: str) -> None:
    run(["uv", "pip", "install", *packages, "--python", str(venv_python(venv_name))])


# ── 系統工具檢查 ──────────────────────────────────────────────────────────────

def check_chrome() -> bool:
    if sys.platform == "darwin":
        return any(p.exists() for p in [
            Path("/Applications/Google Chrome.app"),
            Path("/Applications/Chromium.app"),
        ])
    if sys.platform == "win32":
        return any(p.exists() for p in [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ])
    return which("google-chrome") or which("chromium")


def check_system() -> dict[str, bool]:
    return {
        "uv":     which("uv"),
        "ffmpeg": which("ffmpeg"),
        "node":   which("node"),
        "marp":   which("marp"),
        "chrome": check_chrome(),
    }


def ok(label: str, good: bool, hint: str = "") -> None:
    icon = "✅" if good else "❌"
    msg = f"  {icon} {label}"
    if hint and not good:
        msg += f"  →  {hint}"
    print(msg)


# ── 主流程 ────────────────────────────────────────────────────────────────────

def cmd_check() -> None:
    print("=== 環境檢查 ===")
    print(f"平台：{sys.platform} / {platform.machine()}")
    print(f"Apple Silicon：{'是' if is_apple_silicon() else '否'}")
    print(f"venv 目錄：{VENV_DIR}")
    print()

    print("[ 系統工具 ]")
    hints = {
        "uv":     "安裝：https://docs.astral.sh/uv/",
        "ffmpeg": "Mac: brew install ffmpeg  |  Win: winget install ffmpeg",
        "node":   "安裝：https://nodejs.org/",
        "marp":   "npm install -g @marp-team/marp-cli",
        "chrome": "Mac: brew install --cask google-chrome  |  Win: winget install Google.Chrome",
    }
    for tool, good in check_system().items():
        ok(tool, good, hints[tool])

    print()
    print("[ Whisper 後端 ]")
    if is_apple_silicon():
        print("  → mlx-whisper（Apple Silicon 原生，模型 whisper-large-v3-turbo）")
    else:
        print("  → faster-whisper（跨平台 CPU/CUDA，模型 medium，約 1.5 GB）")

    print()
    print("[ Python venv ]")
    for name in ("tts", "whisper", "piper", "melo"):
        py = venv_python(name)
        ok(f"venv/{name}/", py.exists(), f"尚未安裝，執行 python setup.py 以建立")


def cmd_install() -> None:
    print("=== ai-video-maker 安裝 ===")
    print(f"平台：{sys.platform} / {platform.machine()}")
    print(f"Apple Silicon：{'是' if is_apple_silicon() else '否'}")
    print(f"安裝位置：{VENV_DIR}")
    print()

    checks = check_system()
    if not checks["uv"]:
        print("❌ 請先安裝 uv：https://docs.astral.sh/uv/")
        print("   Mac：curl -Ls https://astral.sh/uv/install.sh | sh")
        print("   Win：powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        sys.exit(1)

    VENV_DIR.mkdir(parents=True, exist_ok=True)

    # Edge TTS
    print("[ 1/4 ] 安裝 Edge TTS...")
    uv_create_venv("tts")
    uv_install("tts", "edge-tts")
    print("  ✅ edge-tts 安裝完成\n")

    # Whisper
    print("[ 2/4 ] 安裝 Whisper（字幕辨識）...")
    uv_create_venv("whisper")
    if is_apple_silicon():
        print("  → Apple Silicon：安裝 mlx-whisper + opencc")
        uv_install("whisper", "mlx-whisper", "opencc-python-reimplemented")
        print("  ✅ mlx-whisper + opencc 安裝完成")
        print("  ℹ️  首次執行時會自動下載模型（約 1 GB）")
    else:
        print("  → 非 Apple Silicon：安裝 faster-whisper + opencc")
        uv_install("whisper", "faster-whisper", "opencc-python-reimplemented")
        print("  ✅ faster-whisper + opencc 安裝完成")
        print("  ℹ️  首次執行時會自動下載模型（約 1.5 GB）")
    print()

    # Piper TTS
    print("[ 3/4 ] 安裝 Piper TTS（本地語音，CPU 快速）...")
    uv_create_venv("piper")
    uv_install("piper", "piper-tts")
    print("  ✅ piper-tts 安裝完成")
    print("  ℹ️  需下載模型才能使用：python prepare_offline.py --piper-only\n")

    # MeloTTS
    print("[ 4/4 ] 安裝 MeloTTS（本地語音，CPU 中速）...")
    print("  → 安裝 melo-tts（含 PyTorch CPU，約 300 MB，請稍候）...")
    uv_create_venv("melo")
    uv_install("melo", "melo-tts")
    print("  ✅ melo-tts 安裝完成")
    print("  ℹ️  首次執行時會自動下載模型（約 300 MB）\n")

    # 系統工具提醒
    missing = [t for t, good in checks.items() if not good and t != "uv"]
    if missing:
        is_win = sys.platform == "win32"
        install_hints = {
            "ffmpeg": ("brew install ffmpeg",                  "winget install ffmpeg"),
            "node":   ("brew install node",                    "winget install OpenJS.NodeJS"),
            "marp":   ("npm install -g @marp-team/marp-cli",   "npm install -g @marp-team/marp-cli"),
            "chrome": ("brew install --cask google-chrome",    "winget install Google.Chrome"),
        }
        print("[ 系統工具 ]（需手動安裝）")
        for t in missing:
            cmd = install_hints[t][1 if is_win else 0]
            print(f"  ⚠️  {t}：{cmd}")

        if "marp" in missing:
            print()
            if is_win:
                print("  ────────────────────────────────────────────────────")
                print("  ⚠️  marp 安裝步驟（Windows）：")
                print()
                print("  1. 確認 Node.js 已安裝（需 v18+）：")
                if not checks.get("node"):
                    print("     → 官網下載（LTS 版）：https://nodejs.org/")
                    print("       或：winget install OpenJS.NodeJS")
                else:
                    print("     ✅ node 已安裝")
                print()
                print("  2. 安裝 marp-cli（需網路，約 200 MB）：")
                print("     npm install -g @marp-team/marp-cli")
                print()
                print("  3. 確認安裝成功（開新命令提示字元後執行）：")
                print("     marp --version")
                print()
                print("  ℹ️  公司電腦若無法使用 npm install -g，請洽 IT 協助安裝 Node.js，")
                print("      或使用 npx（每次執行需下載，較慢）。")
                print("  ────────────────────────────────────────────────────")
            else:
                print("  ────────────────────────────────────────────────────")
                print("  ⚠️  marp 安裝步驟（macOS）：")
                print("  1. brew install node   （已有 node 可跳過）")
                print("  2. npm install -g @marp-team/marp-cli")
                print("  3. marp --version      （確認安裝成功）")
                print("  ────────────────────────────────────────────────────")
        print()

    print("=== 安裝完成 ===")
    print(f"使用方式：python make_video.py <影片目錄>")
    print(f"環境檢查：python setup.py --check")
    print(f"範例：    python make_video.py ./example/")


def main() -> None:
    parser = argparse.ArgumentParser(description="ai-video-maker 安裝腳本")
    parser.add_argument("--check", action="store_true", help="只檢查環境，不安裝")
    args = parser.parse_args()
    cmd_check() if args.check else cmd_install()


if __name__ == "__main__":
    main()
