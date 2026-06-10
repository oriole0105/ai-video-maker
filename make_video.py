#!/usr/bin/env python3
"""make_video.py — 教學影片自動化工具

Usage:
  python make_video.py <output_dir>
  python make_video.py --voice zh-TW-YunJheNeural --rate "+20%" <output_dir>

Expects in output_dir:
  slides.md                          — Marp 投影片來源
  narration_01.txt .. narration_NN.txt — 每頁旁白（純文字）

Produces:
  slides.001.png .. slides.NNN.png   — 投影片圖片
  slides.pdf                         — 投影片 PDF（供文件分享）
  audio_01.mp3 .. audio_NN.mp3       — TTS 語音
  segment_01.mp4 .. segment_NN.mp4   — 每頁影片片段
  concat_list.txt                    — FFmpeg concat 清單
  final.srt                          — 字幕（Whisper 辨識）
  final.mp4                          — 最終影片（含字幕軌）
"""

import argparse
import html
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ── 路徑設定（所有 venv 都在本專案的 venv/ 目錄下）──────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_DIR = SCRIPT_DIR / "venv"


def _venv_bin(venv_name: str, exe: str) -> Path:
    base = VENV_DIR / venv_name
    if sys.platform == "win32":
        for name in (exe + ".exe", exe):
            p = base / "Scripts" / name
            if p.exists():
                return p
        return base / "Scripts" / exe
    return base / "bin" / exe


def _is_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"


def _marp_exe() -> list[str]:
    """Windows npm CLIs install as .cmd scripts; wrap with 'cmd /c' to execute without shell=True."""
    if sys.platform == "win32":
        marp = shutil.which("marp")
        return ["cmd", "/c", marp if marp else "marp"]
    return ["marp"]


# ── TTS 設定 ─────────────────────────────────────────────────────────────────

EDGE_TTS_BIN = _venv_bin("tts", "edge-tts")
DEFAULT_VOICE = "zh-TW-HsiaoChenNeural"
DEFAULT_RATE = "+0%"

# Azure TTS 設定
AZURE_DEFAULT_VOICE = "zh-TW-HsiaoChenNeural"
AZURE_DEFAULT_REGION = "eastasia"

# ── Whisper 設定 ─────────────────────────────────────────────────────────────

WHISPER_PYTHON = _venv_bin("whisper", "python")
WHISPER_MODEL_MLX = "mlx-community/whisper-large-v3-turbo"
_offline_model = SCRIPT_DIR / "offline_pack" / "whisper_model"
WHISPER_MODEL_FAST = str(_offline_model) if (_offline_model / "model.bin").exists() else "medium"

WHISPER_SCRIPT_MLX = """
import sys, json
import mlx_whisper, opencc
audio, model = sys.argv[1], sys.argv[2]
result = mlx_whisper.transcribe(audio, path_or_hf_repo=model, language='zh')
converter = opencc.OpenCC('s2twp')
segs = [{"start": s["start"], "end": s["end"],
         "text": converter.convert(s["text"].strip())}
        for s in result["segments"]]
print(json.dumps(segs, ensure_ascii=False))
"""

WHISPER_SCRIPT_FAST = """
import sys, json
from faster_whisper import WhisperModel
import opencc
audio, model_size = sys.argv[1], sys.argv[2]
model = WhisperModel(model_size, device="cpu", compute_type="int8")
converter = opencc.OpenCC('s2twp')
segments, _ = model.transcribe(audio, language="zh", beam_size=5)
segs = [{"start": s.start, "end": s.end,
         "text": converter.convert(s.text.strip())}
        for s in segments]
print(json.dumps(segs, ensure_ascii=False))
"""

# ── Piper TTS 設定 ────────────────────────────────────────────────────────────

PIPER_PYTHON = _venv_bin("piper", "python")
PIPER_MODEL = SCRIPT_DIR / "offline_pack" / "piper_model" / "zh_CN-huayan-medium.onnx"

PIPER_SCRIPT = """
import sys, wave, numpy as np
from piper.voice import PiperVoice, SynthesisConfig
model_path, text_file, wav_file, length_scale = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
voice = PiperVoice.load(model_path)
text = open(text_file, encoding='utf-8').read().strip()
cfg = SynthesisConfig(length_scale=length_scale)
chunks = list(voice.synthesize(text, syn_config=cfg))
with wave.open(wav_file, 'wb') as wf:
    wf.setnchannels(chunks[0].sample_channels)
    wf.setsampwidth(chunks[0].sample_width)
    wf.setframerate(chunks[0].sample_rate)
    for c in chunks:
        wf.writeframes((c.audio_float_array * 32767).astype(np.int16).tobytes())
"""

# ── MeloTTS 設定 ──────────────────────────────────────────────────────────────

MELO_PYTHON = _venv_bin("melo", "python")

MELO_SCRIPT = """
import sys
from melo.api import TTS
text_file, wav_file = sys.argv[1], sys.argv[2]
text = open(text_file, encoding='utf-8').read().strip()
tts = TTS(language='ZH', device='cpu')
speaker_ids = tts.hps.data.spk2id
spk = speaker_ids.get('ZH', list(speaker_ids.values())[0])
tts.tts_to_file(text, spk, wav_file, speed=1.0)
"""


# ── 輔助函式 ─────────────────────────────────────────────────────────────────

def run(cmd: list[str], *, quiet: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=quiet, text=True, check=True)
    except FileNotFoundError:
        print(f"  錯誤：找不到指令 {cmd[0]}", file=sys.stderr)
        print("  請確認系統工具已安裝：ffmpeg / marp / node", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"  錯誤：執行失敗 {' '.join(str(c) for c in cmd)}", file=sys.stderr)
        if e.stderr:
            print(f"  stderr: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def srt_timestamp(sec: float) -> str:
    ms = int((sec % 1) * 1000)
    s = int(sec) % 60
    m = int(sec) // 60 % 60
    h = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def find_narration_files(d: Path) -> list[Path]:
    return sorted(d.glob("narration_*.txt"))


def find_audio(d: Path, idx: str) -> Path | None:
    for ext in ("mp3", "wav"):
        p = d / f"audio_{idx}.{ext}"
        if p.exists():
            return p
    return None


# ── Pipeline 步驟 ─────────────────────────────────────────────────────────────

def step_marp(output_dir: Path) -> int:
    print("[1/5] 投影片 → 圖片 + PDF（Marp）...")
    themes_dir = SCRIPT_DIR / "themes"
    theme_args = ["--theme-set", str(themes_dir)] if themes_dir.is_dir() else []
    base = _marp_exe() + [str(output_dir / "slides.md"), "--allow-local-files"] + theme_args

    try:
        p_png = subprocess.Popen(
            base + ["--images", "png", "--image-scale", "2",
                    "-o", str(output_dir / "slides.png")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        p_pdf = subprocess.Popen(
            base + ["--pdf", "-o", str(output_dir / "slides.pdf")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
    except FileNotFoundError:
        print("  錯誤：找不到 marp，請確認已安裝 @marp-team/marp-cli", file=sys.stderr)
        print("  Windows 請先安裝 Node.js，再執行：npm install -g @marp-team/marp-cli", file=sys.stderr)
        sys.exit(1)

    for p, label in [(p_png, "PNG"), (p_pdf, "PDF")]:
        _, stderr = p.communicate()
        if p.returncode != 0:
            print(f"  錯誤：Marp {label} 生成失敗", file=sys.stderr)
            if stderr:
                print(f"  {stderr.strip()}", file=sys.stderr)
            sys.exit(1)

    count = len(sorted(output_dir.glob("slides.*.png")))
    print(f"  完成，共 {count} 張圖片，已同步產生 slides.pdf。")
    return count


def _ssml_wrap(text: str, voice: str, rate: str) -> str:
    """純文字自動包成 SSML；已是 <speak> 開頭則直接使用（支援手寫 <phoneme>）。"""
    text = text.strip()
    if text.lower().startswith("<speak"):
        return text
    content = html.escape(text)
    if rate and rate != "+0%":
        content = f'<prosody rate="{rate}">{content}</prosody>'
    return (
        f'<speak version="1.0" '
        f'xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">\n'
        f'  <voice name="{voice}">{content}</voice>\n'
        f'</speak>'
    )


def step_tts_azure(output_dir: Path, narrations: list[Path],
                   api_key: str, region: str, voice: str, rate: str) -> None:
    """使用 Azure Speech REST API 合成語音。"""
    print(f"[2/5] 旁白 → 語音（Azure Speech，聲音：{voice}）...")
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    for nf in narrations:
        idx = nf.stem.split("_")[-1]
        audio_file = output_dir / f"audio_{idx}.mp3"
        print(f"  生成 audio_{idx}.mp3 ...")
        ssml = _ssml_wrap(nf.read_text(encoding="utf-8"), voice, rate)
        req = urllib.request.Request(
            url,
            data=ssml.encode("utf-8"),
            headers={
                "Ocp-Apim-Subscription-Key": api_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                audio_file.write_bytes(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  錯誤：Azure TTS HTTP {e.code}: {body}", file=sys.stderr)
            sys.exit(1)
    print("  完成。")


def _rate_to_length_scale(rate: str) -> float:
    """Convert '+30%' style rate to piper length_scale (< 1 = faster)."""
    import re
    m = re.match(r'([+-]?\d+)%', rate.strip())
    if m:
        speed = 1.0 + int(m.group(1)) / 100.0
        return 1.0 / speed
    return 1.0


def step_tts_piper(output_dir: Path, narrations: list[Path], rate: str = "+0%") -> None:
    length_scale = _rate_to_length_scale(rate)
    print(f"[2/5] 旁白 → 語音（Piper TTS，語速：{rate}，length_scale={length_scale:.3f}）...")
    if not PIPER_PYTHON.exists():
        print("  錯誤：找不到 piper venv，請先執行 python setup.py", file=sys.stderr)
        sys.exit(1)
    if not PIPER_MODEL.exists():
        print(f"  錯誤：找不到 Piper 模型：{PIPER_MODEL}", file=sys.stderr)
        print("  請執行：python prepare_offline.py --piper-only", file=sys.stderr)
        sys.exit(1)
    for nf in narrations:
        idx = nf.stem.split("_")[-1]
        wav = output_dir / f"audio_{idx}.wav"
        mp3 = output_dir / f"audio_{idx}.mp3"
        print(f"  生成 audio_{idx}.mp3 ...")
        subprocess.run(
            [str(PIPER_PYTHON), "-c", PIPER_SCRIPT,
             str(PIPER_MODEL), str(nf), str(wav), str(length_scale)],
            capture_output=True, check=True,
        )
        run(["ffmpeg", "-y", "-i", str(wav), str(mp3)])
        wav.unlink(missing_ok=True)
    print("  完成。")


def step_tts_melo(output_dir: Path, narrations: list[Path]) -> None:
    print("[2/5] 旁白 → 語音（MeloTTS）...")
    if not MELO_PYTHON.exists():
        print("  錯誤：找不到 melo venv，請先執行 python setup.py", file=sys.stderr)
        sys.exit(1)
    for nf in narrations:
        idx = nf.stem.split("_")[-1]
        wav = output_dir / f"audio_{idx}.wav"
        mp3 = output_dir / f"audio_{idx}.mp3"
        print(f"  生成 audio_{idx}.mp3 ...")
        subprocess.run(
            [str(MELO_PYTHON), "-c", MELO_SCRIPT, str(nf), str(wav)],
            capture_output=True, check=True,
        )
        run(["ffmpeg", "-y", "-i", str(wav), str(mp3)])
        wav.unlink(missing_ok=True)
    print("  完成。")


def step_tts(output_dir: Path, narrations: list[Path], voice: str, rate: str) -> None:
    print(f"[2/5] 旁白 → 語音（Edge TTS，聲音：{voice}）...")
    for nf in narrations:
        idx = nf.stem.split("_")[-1]
        out = output_dir / f"audio_{idx}.mp3"
        print(f"  生成 audio_{idx}.mp3 ...")
        run([str(EDGE_TTS_BIN), "--voice", voice, "--rate", rate,
             "-f", str(nf), "--write-media", str(out)])
    print("  完成。")


def step_segments(output_dir: Path, narrations: list[Path]) -> list[Path]:
    print("[3/5] 每頁合成影片片段（FFmpeg）...")
    segments = []
    for nf in narrations:
        idx = nf.stem.split("_")[-1]
        n = int(idx)
        img = output_dir / f"slides.{n:03d}.png"
        audio = find_audio(output_dir, idx)
        seg = output_dir / f"segment_{idx}.mp4"

        if not img.exists():
            print(f"  警告：找不到 {img.name}，跳過")
            continue
        if audio is None:
            print(f"  警告：找不到 audio_{idx}，跳過")
            continue

        print(f"  生成 segment_{idx}.mp4 ...")
        run([
            "ffmpeg", "-y", "-loop", "1",
            "-i", str(img), "-i", str(audio),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                   "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(seg),
        ])
        segments.append(seg)
    print("  完成。")
    return segments


def step_concat(output_dir: Path, segments: list[Path]) -> Path:
    print("[4/5] 串接所有片段（FFmpeg）...")
    concat = output_dir / "concat_list.txt"
    concat.write_text("\n".join(f"file '{s.name}'" for s in segments) + "\n",
                      encoding="utf-8")
    final = output_dir / "final.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "aresample=async=1",
        str(final),
    ])
    print("  完成。")
    return final


def step_srt(output_dir: Path) -> Path:
    final = output_dir / "final.mp4"
    srt = output_dir / "final.srt"

    if not WHISPER_PYTHON.exists():
        print("[5/5] 跳過字幕（Whisper venv 未安裝）")
        return srt

    backend = "mlx-whisper" if _is_apple_silicon() else "faster-whisper"
    print(f"[5/5] 語音辨識字幕（{backend}）...")

    if _is_apple_silicon():
        script, model_arg = WHISPER_SCRIPT_MLX, WHISPER_MODEL_MLX
    else:
        script, model_arg = WHISPER_SCRIPT_FAST, WHISPER_MODEL_FAST

    print("  辨識 final.mp4 音軌中...")
    r = subprocess.run(
        [str(WHISPER_PYTHON), "-c", script, str(final), model_arg],
        capture_output=True, text=True, check=True,
    )
    segs = json.loads(r.stdout.strip())

    lines = []
    for i, seg in enumerate(segs, 1):
        lines += [str(i),
                  f"{srt_timestamp(seg['start'])} --> {srt_timestamp(seg['end'])}",
                  seg["text"], ""]
    srt.write_text("\n".join(lines), encoding="utf-8")

    # 嵌入字幕軌
    tmp = output_dir / "final_sub.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(final), "-i", str(srt),
         "-map", "0:v", "-map", "0:a", "-map", "1:s",
         "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=zho", str(tmp)],
        capture_output=True, check=True,
    )
    tmp.replace(final)
    print(f"  完成。字幕已嵌入 final.mp4")
    return srt


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="教學影片自動化工具")
    parser.add_argument("output_dir", help="含 slides.md 和 narration_*.txt 的目錄")
    parser.add_argument("--marp-only", action="store_true",
                        help="只重新生成投影片圖片（Marp），不跑 TTS 或影片合成")
    parser.add_argument("--concat-only", action="store_true",
                        help="跳過 TTS，直接串接現有 segment_*.mp4（已有片段時使用）")
    parser.add_argument("--tts", choices=["edge", "azure", "piper", "melo"],
                        default=os.environ.get("MAKE_VIDEO_TTS", "edge"),
                        help="TTS 後端：edge（預設）、azure、piper、melo")
    parser.add_argument("--voice", default=os.environ.get("MAKE_VIDEO_VOICE", DEFAULT_VOICE),
                        help=f"Edge TTS 聲音（預設：{DEFAULT_VOICE}）")
    parser.add_argument("--rate", default=os.environ.get("MAKE_VIDEO_RATE", DEFAULT_RATE),
                        help="語速（預設：+0%%，加速可用 +20%%）")
    # Azure TTS 選項
    parser.add_argument("--azure-key",
                        default=os.environ.get("AZURE_SPEECH_KEY", ""),
                        help="Azure Speech API key（或設 AZURE_SPEECH_KEY 環境變數）")
    parser.add_argument("--azure-region",
                        default=os.environ.get("AZURE_SPEECH_REGION", AZURE_DEFAULT_REGION),
                        help=f"Azure region（預設：{AZURE_DEFAULT_REGION}）")
    parser.add_argument("--azure-voice",
                        default=os.environ.get("AZURE_SPEECH_VOICE", AZURE_DEFAULT_VOICE),
                        help=f"Azure TTS 聲音（預設：{AZURE_DEFAULT_VOICE}）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()

    if not output_dir.is_dir():
        print(f"錯誤：目錄不存在：{output_dir}", file=sys.stderr)
        sys.exit(1)

    # ── marp-only 模式 ────────────────────────────────────────────────────────
    if args.marp_only:
        if not (output_dir / "slides.md").exists():
            print(f"錯誤：找不到 slides.md：{output_dir}", file=sys.stderr)
            sys.exit(1)
        step_marp(output_dir)
        return

    # ── concat-only 模式 ──────────────────────────────────────────────────────
    if args.concat_only:
        segments = sorted(output_dir.glob("segment_*.mp4"))
        if not segments:
            print(f"錯誤：找不到 segment_*.mp4，請先執行完整生成流程", file=sys.stderr)
            sys.exit(1)
        print("=== 合併模式（concat-only）===")
        print(f"目錄：{output_dir}")
        print(f"片段數：{len(segments)}")
        print()
        final = step_concat(output_dir, segments)
        print()
        srt = step_srt(output_dir)
        print()
        size = final.stat().st_size
        size_str = f"{size / (1024**2):.1f} MB" if size >= 1024**2 else f"{size / 1024:.1f} KB"
        print("=== 完成 ===")
        print(f"影片：{final}")
        print(f"大小：{size_str}")
        return

    # ── 完整流程 ──────────────────────────────────────────────────────────────
    if not (output_dir / "slides.md").exists():
        print(f"錯誤：找不到 slides.md：{output_dir}", file=sys.stderr)
        sys.exit(1)

    narrations = find_narration_files(output_dir)
    if not narrations:
        print(f"錯誤：目錄中沒有 narration_*.txt：{output_dir}", file=sys.stderr)
        sys.exit(1)

    if args.tts == "azure":
        if not args.azure_key:
            print("錯誤：--azure-key 必填（或設 AZURE_SPEECH_KEY 環境變數）", file=sys.stderr)
            sys.exit(1)
    elif args.tts == "edge" and not EDGE_TTS_BIN.exists():
        print("錯誤：找不到 edge-tts，請先執行 python setup.py", file=sys.stderr)
        sys.exit(1)

    print("=== make_video.py ===")
    print(f"目錄：{output_dir}")
    print(f"頁數：{len(narrations)}")
    if args.tts == "azure":
        print(f"聲音：{args.azure_voice}  Region：{args.azure_region}  語速：{args.rate}")
    else:
        print(f"聲音：{args.voice}  語速：{args.rate}")
    print()

    step_marp(output_dir)
    print()
    if args.tts == "azure":
        step_tts_azure(output_dir, narrations,
                       args.azure_key, args.azure_region,
                       args.azure_voice, args.rate)
    elif args.tts == "piper":
        step_tts_piper(output_dir, narrations, args.rate)
    elif args.tts == "melo":
        step_tts_melo(output_dir, narrations)
    else:
        step_tts(output_dir, narrations, args.voice, args.rate)
    print()
    segments = step_segments(output_dir, narrations)
    print()
    if not segments:
        print("錯誤：沒有產生任何影片片段", file=sys.stderr)
        sys.exit(1)
    final = step_concat(output_dir, segments)
    print()
    srt = step_srt(output_dir)
    print()

    size = final.stat().st_size
    size_str = f"{size / (1024**2):.1f} MB" if size >= 1024**2 else f"{size / 1024:.1f} KB"
    print("=== 完成 ===")
    print(f"影片：{final}")
    print(f"字幕：{srt}")
    print(f"大小：{size_str}")


if __name__ == "__main__":
    main()
