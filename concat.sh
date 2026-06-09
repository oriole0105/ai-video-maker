#!/usr/bin/env bash
# concat.sh — 只合併現有片段（跳過 TTS，適合微調後重新合成）
#
# 使用時機：
#   已經跑過 generate.sh，只修改了少數片段，不想重新跑語音合成
#
# 用法：
#   ./concat.sh                     # 使用 example/ 資料夾
#   ./concat.sh ./my_lesson/        # 指定你的影片資料夾

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:-$SCRIPT_DIR/example}"

python3 "$SCRIPT_DIR/make_video.py" --concat-only "$DIR"
