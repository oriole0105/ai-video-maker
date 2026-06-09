#!/usr/bin/env bash
# generate.sh — 生成教學影片（完整流程：投影片→語音→影片→字幕）
#
# 用法：
#   ./generate.sh                   # 使用 example/ 資料夾（示範用）
#   ./generate.sh ./my_lesson/      # 指定你的影片資料夾
#   ./generate.sh ./my_lesson/ --rate "+20%"   # 加快語速

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:-$SCRIPT_DIR/example}"
shift 2>/dev/null || true   # 移除第一個參數，剩下的傳給 make_video.py

python3 "$SCRIPT_DIR/make_video.py" "$DIR" "$@"
