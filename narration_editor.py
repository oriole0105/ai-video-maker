#!/usr/bin/env python3
"""narration_editor.py — 投影片旁白瀏覽器編輯器

Usage:
  python narration_editor.py <output_dir>
  python narration_editor.py --port 8765 <output_dir>

開啟後自動在瀏覽器顯示投影片縮圖與旁白，可直接編輯、儲存，
並呼叫 make_video.py 生成影片。
"""

import argparse
import json
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

MAKE_VIDEO_PY = Path(__file__).parent / "make_video.py"

HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>旁白編輯器</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         height: 100vh; display: flex; flex-direction: column; background: #f3f4f6; }

  header {
    padding: 10px 20px;
    background: #1e40af;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    gap: 12px;
  }
  header .title { font-weight: 700; font-size: 16px; white-space: nowrap; }
  header .dir-path { font-size: 12px; opacity: 0.7; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  header .right { display: flex; gap: 10px; align-items: center; flex-shrink: 0; }

  .main { display: flex; flex: 1; overflow: hidden; }

  /* Sidebar */
  .sidebar {
    width: 180px;
    overflow-y: auto;
    background: white;
    border-right: 1px solid #e5e7eb;
    flex-shrink: 0;
  }
  .thumb {
    padding: 8px;
    cursor: pointer;
    border-bottom: 1px solid #f3f4f6;
    transition: background 0.1s;
  }
  .thumb:hover { background: #eff6ff; }
  .thumb.active { background: #dbeafe; border-left: 3px solid #2563eb; }
  .thumb img { width: 100%; display: block; border: 1px solid #e5e7eb; border-radius: 3px; }
  .thumb .page-num { font-size: 10px; color: #9ca3af; margin: 3px 0 2px; }
  .thumb .preview {
    font-size: 11px; color: #6b7280; line-height: 1.4;
    overflow: hidden; display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  }
  .thumb .unsaved-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #f59e0b; display: inline-block; margin-left: 4px; vertical-align: middle;
  }

  /* Editor panel */
  .editor-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    gap: 14px;
    overflow: hidden;
  }
  .empty-state {
    margin: auto;
    text-align: center;
    color: #9ca3af;
  }

  .slide-image-wrap {
    flex: 1;
    min-height: 0;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  .slide-image-wrap img {
    max-height: 100%;
    max-width: 100%;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    object-fit: contain;
  }

  .narration-section { flex-shrink: 0; display: flex; flex-direction: column; gap: 8px; }
  .narration-label { font-size: 13px; font-weight: 600; color: #374151; }
  textarea {
    resize: none;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    line-height: 1.6;
    font-family: inherit;
    background: white;
    height: 110px;
  }
  textarea:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px #bfdbfe; }

  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-shrink: 0;
  }
  .char-count { font-size: 13px; color: #9ca3af; }
  .save-status { font-size: 13px; }
  .save-status.saved { color: #059669; }
  .save-status.unsaved { color: #f59e0b; }
  .save-status.error { color: #dc2626; }

  /* Buttons */
  button {
    padding: 7px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: background 0.15s;
  }
  button:disabled { opacity: 0.5; cursor: default; }
  .btn-save { background: #2563eb; color: white; }
  .btn-save:hover:not(:disabled) { background: #1d4ed8; }
  .btn-generate { background: #059669; color: white; }
  .btn-generate:hover:not(:disabled) { background: #047857; }
  .gen-status { font-size: 13px; }
  .gen-status.success { color: #6ee7b7; }
  .gen-status.error { color: #fca5a5; }

  /* Nav buttons */
  .nav-btns { display: flex; gap: 6px; }
  .btn-nav { background: rgba(255,255,255,0.15); color: white; padding: 5px 12px; }
  .btn-nav:hover:not(:disabled) { background: rgba(255,255,255,0.25); }
</style>
</head>
<body>

<header>
  <div style="display:flex; align-items:center; gap:12px; overflow:hidden;">
    <span class="title">旁白編輯器</span>
    <span class="dir-path" id="dirPath"></span>
  </div>
  <div class="right">
    <div class="nav-btns">
      <button class="btn-nav" id="prevBtn" onclick="navigate(-1)" disabled>‹ 上一頁</button>
      <button class="btn-nav" id="nextBtn" onclick="navigate(1)" disabled>下一頁 ›</button>
    </div>
    <span class="gen-status" id="genStatus"></span>
    <button class="btn-generate" id="genBtn" onclick="generateVideo()">▶ 生成影片</button>
  </div>
</header>

<div class="main">
  <div class="sidebar" id="sidebar"></div>
  <div class="editor-panel" id="editorPanel">
    <div class="empty-state">
      <div style="font-size: 48px; margin-bottom: 12px;">←</div>
      <div>點選左側投影片開始編輯</div>
    </div>
  </div>
</div>

<script>
let slides = [];
let currentIdx = null;
let unsaved = new Set();

async function loadSlides() {
  const res = await fetch('/api/slides');
  const data = await res.json();
  slides = data.slides;
  document.getElementById('dirPath').textContent = data.dir;
  renderSidebar();
  if (slides.length > 0) selectSlide(0);
}

function renderSidebar() {
  const sb = document.getElementById('sidebar');
  sb.innerHTML = slides.map((s, i) => `
    <div class="thumb ${i === currentIdx ? 'active' : ''}" onclick="selectSlide(${i})" id="thumb-${i}">
      <img src="/api/slide/${s.idx}/image" loading="lazy" />
      <div class="page-num">第 ${s.idx} 頁${unsaved.has(i) ? '<span class="unsaved-dot"></span>' : ''}</div>
      <div class="preview" id="preview-${i}">${s.narration || '（無旁白）'}</div>
    </div>
  `).join('');
}

function updateThumbActive() {
  document.querySelectorAll('.thumb').forEach((el, j) => {
    el.classList.toggle('active', j === currentIdx);
  });
}

function selectSlide(i) {
  if (currentIdx !== null && unsaved.has(currentIdx)) {
    const ta = document.getElementById('narration');
    if (ta) saveNarration(slides[currentIdx].idx, ta.value, false);
  }

  currentIdx = i;
  updateThumbActive();

  const thumb = document.getElementById('thumb-' + i);
  if (thumb) thumb.scrollIntoView({ block: 'nearest' });

  document.getElementById('prevBtn').disabled = i === 0;
  document.getElementById('nextBtn').disabled = i === slides.length - 1;

  const s = slides[i];
  document.getElementById('editorPanel').innerHTML = `
    <div class="slide-image-wrap">
      <img src="/api/slide/${s.idx}/image" alt="第 ${s.idx} 頁" />
    </div>
    <div class="narration-section">
      <div class="narration-label">第 ${s.idx} 頁旁白</div>
      <textarea id="narration" oninput="onTextChange(${i})">${escapeHtml(s.narration || '')}</textarea>
      <div class="toolbar">
        <button class="btn-save" id="saveBtn" onclick="saveFromBtn(${s.idx}, ${i})">儲存</button>
        <span class="char-count" id="charCount">${(s.narration || '').length} 字</span>
        <span class="save-status" id="saveStatus"></span>
      </div>
    </div>
  `;
  document.getElementById('narration').focus();
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function onTextChange(i) {
  const text = document.getElementById('narration').value;
  document.getElementById('charCount').textContent = text.length + ' 字';
  document.getElementById('saveStatus').textContent = '● 未儲存';
  document.getElementById('saveStatus').className = 'save-status unsaved';
  slides[i].narration = text;
  unsaved.add(i);
  const preview = document.getElementById('preview-' + i);
  if (preview) preview.textContent = text || '（無旁白）';
  const pnum = document.querySelector(`#thumb-${i} .page-num`);
  if (pnum && !pnum.querySelector('.unsaved-dot')) {
    pnum.innerHTML += '<span class="unsaved-dot"></span>';
  }
}

async function saveNarration(idx, text, showFeedback = true) {
  const res = await fetch(`/api/slide/${idx}/narration`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });

  const i = slides.findIndex(s => s.idx === idx);
  if (i >= 0) unsaved.delete(i);

  const pnum = document.querySelector(`#thumb-${i} .page-num`);
  if (pnum) {
    const dot = pnum.querySelector('.unsaved-dot');
    if (dot) dot.remove();
  }

  if (showFeedback) {
    const status = document.getElementById('saveStatus');
    if (status) {
      if (res.ok) {
        status.textContent = '✓ 已儲存';
        status.className = 'save-status saved';
        setTimeout(() => { if (status) status.textContent = ''; }, 2000);
      } else {
        status.textContent = '✗ 儲存失敗';
        status.className = 'save-status error';
      }
    }
  }
}

async function saveFromBtn(idx, i) {
  const ta = document.getElementById('narration');
  if (ta) await saveNarration(idx, ta.value, true);
}

function navigate(dir) {
  if (currentIdx === null) return;
  const next = currentIdx + dir;
  if (next >= 0 && next < slides.length) selectSlide(next);
}

async function generateVideo() {
  for (const i of unsaved) {
    const s = slides[i];
    await saveNarration(s.idx, s.narration, false);
  }

  const btn = document.getElementById('genBtn');
  const status = document.getElementById('genStatus');
  btn.disabled = true;
  btn.textContent = '生成中...';
  status.textContent = '';

  try {
    const res = await fetch('/api/generate', { method: 'POST' });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = '▶ 生成影片';
    if (data.success) {
      status.textContent = '✓ ' + data.message;
      status.className = 'gen-status success';
    } else {
      status.textContent = '✗ ' + data.message;
      status.className = 'gen-status error';
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = '▶ 生成影片';
    status.textContent = '✗ 連線失敗';
    status.className = 'gen-status error';
  }
}

document.addEventListener('keydown', (e) => {
  if (document.activeElement && document.activeElement.tagName === 'TEXTAREA') {
    if ((e.key === 's' || e.key === 'S') && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (currentIdx !== null) saveFromBtn(slides[currentIdx].idx, currentIdx);
    }
    return;
  }
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') navigate(1);
  else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') navigate(-1);
});

loadSlides();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    output_dir: Path = None

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/slides":
            narration_files = sorted(self.output_dir.glob("narration_*.txt"))
            slides = []
            for nf in narration_files:
                idx = nf.stem.split("_")[-1]
                text = nf.read_text(encoding="utf-8").strip()
                slides.append({"idx": idx, "narration": text})
            self.send_json({"dir": str(self.output_dir), "slides": slides})

        elif path.startswith("/api/slide/") and path.endswith("/image"):
            idx = path.split("/")[3]
            img_path = self.output_dir / f"slides.{int(idx):03d}.png"
            if img_path.exists():
                data = img_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", len(data))
                self.send_header("Cache-Control", "max-age=3600")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path.startswith("/api/slide/") and path.endswith("/narration"):
            idx = path.split("/")[3]
            try:
                text = json.loads(body).get("text", "")
                nf = self.output_dir / f"narration_{idx}.txt"
                nf.write_text(text + "\n", encoding="utf-8")
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/generate":
            try:
                result = subprocess.run(
                    [sys.executable, str(MAKE_VIDEO_PY), str(self.output_dir)],
                    capture_output=True, text=True, timeout=600,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().splitlines()
                    # 相容中文版（大小：）和英文版（File size）輸出
                    summary = next(
                        (l for l in reversed(lines)
                         if "大小：" in l or "File size" in l),
                        "完成"
                    )
                    self.send_json({"success": True, "message": summary})
                else:
                    err = (result.stderr.strip().splitlines() or ["未知錯誤"])[-1]
                    self.send_json({"success": False, "message": err})
            except subprocess.TimeoutExpired:
                self.send_json({"success": False, "message": "逾時（超過 10 分鐘）"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)

        else:
            self.send_response(404)
            self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="投影片旁白編輯器")
    parser.add_argument("output_dir", help="包含 slides.md 和 narration_*.txt 的目錄")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="不自動開啟瀏覽器")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    if not output_dir.is_dir():
        print(f"Error: {output_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    Handler.output_dir = output_dir
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"旁白編輯器：{url}")
    print(f"目錄：{output_dir}")
    print("Ctrl+C 停止")

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止。")


if __name__ == "__main__":
    main()
