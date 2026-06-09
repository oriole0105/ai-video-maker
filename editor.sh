#!/usr/bin/env bash
# editor.sh — 開啟網頁版旁白編輯器
#
# 用法：
#   ./editor.sh                     # 使用 example/ 資料夾（示範用）
#   ./editor.sh ./my_lesson/        # 指定你的影片資料夾

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:-$SCRIPT_DIR/example}"

python3 "$SCRIPT_DIR/narration_editor.py" "$DIR"
