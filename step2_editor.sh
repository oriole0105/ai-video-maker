#!/usr/bin/env bash
# step2_editor.sh — 開啟網頁版旁白編輯器（製作工作台）
#
# 用法：
#   ./step2_editor.sh                     # 使用 example/ 資料夾（示範用）
#   ./step2_editor.sh ./my_lesson/        # 指定你的影片資料夾
#   ./step2_editor.sh ./my_lesson/ 9090   # 指定 port

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:-$SCRIPT_DIR/example}"
PORT="${2:-8765}"

# 先清掉占用同一 port 的舊 process
OLD_PID=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
  echo "清除舊 editor 程序 (PID $OLD_PID, port $PORT)..."
  kill "$OLD_PID" 2>/dev/null || true
  sleep 0.5
fi

echo "啟動製作工作台：$DIR (port $PORT)"
python3 "$SCRIPT_DIR/narration_editor.py" "$DIR" --port "$PORT"
