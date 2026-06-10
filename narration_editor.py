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
import re
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
  .btn-settings { background: rgba(255,255,255,0.15); color: white; padding: 5px 12px; }
  .btn-settings:hover { background: rgba(255,255,255,0.25); }
  .btn-settings.active { background: rgba(255,255,255,0.3); outline: 2px solid rgba(255,255,255,0.4); }

  /* Settings panel */
  .settings-panel {
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: center;
    flex-shrink: 0;
  }
  .settings-group { display: flex; align-items: center; gap: 8px; }
  .settings-label { font-size: 12px; font-weight: 600; color: #64748b; white-space: nowrap; }
  .settings-hint { font-size: 11px; color: #94a3b8; }
  .settings-panel select,
  .settings-panel input[type="text"],
  .settings-panel input[type="password"] {
    padding: 4px 8px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    font-size: 13px;
    background: white;
    font-family: inherit;
  }
  .settings-panel select:focus,
  .settings-panel input:focus { outline: none; border-color: #2563eb; }

  .theme-options { display: flex; gap: 8px; flex-wrap: wrap; }
  .theme-opt {
    display: flex; align-items: center; gap: 5px;
    cursor: pointer; font-size: 12px; color: #374151;
    padding: 4px 8px; border-radius: 5px;
    border: 1px solid #e2e8f0; background: white;
    transition: border-color 0.15s;
    user-select: none;
  }
  .theme-opt:hover { border-color: #94a3b8; }
  .theme-opt input[type="radio"] { display: none; }
  .theme-opt.selected { border-color: #2563eb; background: #eff6ff; font-weight: 600; }
  .theme-swatch { width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; border: 1px solid rgba(0,0,0,0.15); }

  .settings-divider { width: 100%; height: 1px; background: #e2e8f0; margin: 6px 0; }
  .settings-section-label {
    font-size: 10px; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap;
  }
  .btn-refresh {
    padding: 4px 12px; border-radius: 5px; border: 1px solid #cbd5e1;
    background: white; font-size: 12px; font-weight: 500; cursor: pointer;
    color: #374151; transition: all 0.15s;
  }
  .btn-refresh:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }
  .btn-refresh:disabled { opacity: 0.5; cursor: default; }
  .btn-refresh.pending {
    background: #fffbeb; border-color: #f59e0b; color: #92400e; font-weight: 600;
  }
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
    <button class="btn-settings" id="settingsBtn" onclick="toggleSettings()">⚙ 設定</button>
    <button class="btn-generate" id="genBtn" onclick="generateVideo()">▶ 生成影片</button>
  </div>
</header>

<div class="settings-panel" id="settingsPanel" style="display:none">

  <!-- 投影片設定 -->
  <span class="settings-section-label">投影片</span>
  <div class="settings-group">
    <span class="settings-label">主題</span>
    <div class="theme-options" id="themeOptions">
      <label class="theme-opt" data-theme="tech-dark">
        <input type="radio" name="theme" value="tech-dark">
        <span class="theme-swatch" style="background:#1a1a2e;border-color:#3b82f6"></span>科技深藍
      </label>
      <label class="theme-opt" data-theme="clean-light">
        <input type="radio" name="theme" value="clean-light">
        <span class="theme-swatch" style="background:#ffffff;border-color:#94a3b8"></span>清爽白底
      </label>
      <label class="theme-opt" data-theme="corporate-navy">
        <input type="radio" name="theme" value="corporate-navy">
        <span class="theme-swatch" style="background:#f0f4f8;border-color:#2d3748"></span>商務深藍
      </label>
      <label class="theme-opt" data-theme="warm-amber">
        <input type="radio" name="theme" value="warm-amber">
        <span class="theme-swatch" style="background:#1c1208;border-color:#f59e0b"></span>暖琥珀
      </label>
    </div>
  </div>
  <div class="settings-group">
    <button class="btn-refresh" id="refreshBtn" onclick="refreshSlides()">↺ 更新投影片圖片</button>
    <span class="settings-hint" id="themeStatus"></span>
  </div>

  <div class="settings-divider"></div>

  <!-- 影片生成設定 -->
  <span class="settings-section-label">影片生成</span>
  <div class="settings-group">
    <span class="settings-label">TTS 引擎</span>
    <select id="settingTts" onchange="onTtsChange()">
      <option value="edge">Edge TTS（台灣腔，需網路）</option>
      <option value="piper">Piper（離線，普通話）</option>
      <option value="melo">MeloTTS（離線）</option>
      <option value="azure">Azure Speech</option>
    </select>
  </div>
  <div class="settings-group">
    <span class="settings-label">語速</span>
    <input type="text" id="settingRate" value="+0%" style="width:72px">
    <span class="settings-hint">例：+30%、-10%</span>
  </div>
  <div class="settings-group" id="voiceGroup">
    <span class="settings-label">聲音</span>
    <input type="text" id="settingVoice" value="zh-TW-HsiaoChenNeural" style="width:230px">
  </div>
  <div class="settings-group" id="azureKeyGroup" style="display:none">
    <span class="settings-label">Azure Key</span>
    <input type="password" id="settingAzureKey" placeholder="Subscription Key" style="width:200px">
  </div>
  <div class="settings-group" id="azureRegionGroup" style="display:none">
    <span class="settings-label">Region</span>
    <input type="text" id="settingAzureRegion" value="eastasia" style="width:100px">
  </div>

</div>

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
let imageVersion = Date.now();

function initTheme(current) {
  document.querySelectorAll('.theme-opt').forEach(label => {
    const val = label.dataset.theme;
    label.classList.toggle('selected', val === current);
    label.querySelector('input').checked = (val === current);
    label.onclick = () => applyTheme(val);
  });
}

async function applyTheme(theme) {
  document.querySelectorAll('.theme-opt').forEach(label => {
    label.classList.toggle('selected', label.dataset.theme === theme);
    label.querySelector('input').checked = (label.dataset.theme === theme);
  });
  const status = document.getElementById('themeStatus');
  try {
    const res = await fetch('/api/theme', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme }),
    });
    if (res.ok) {
      status.textContent = '主題已儲存，點「↺ 更新投影片圖片」重新生圖';
      status.style.color = '#d97706';
      const btn = document.getElementById('refreshBtn');
      if (btn) btn.classList.add('pending');
    }
  } catch {
    status.textContent = '✗ 套用失敗';
    status.style.color = '#dc2626';
  }
}

async function refreshSlides() {
  const btn = document.getElementById('refreshBtn');
  const status = document.getElementById('themeStatus');
  btn.disabled = true;
  btn.textContent = '↺ 更新中…';
  status.textContent = '';
  try {
    const res = await fetch('/api/refresh-slides', { method: 'POST' });
    if (res.ok) {
      reloadImages();
      btn.classList.remove('pending');
      status.textContent = '✓ 投影片圖片已更新';
      status.style.color = '#059669';
      setTimeout(() => { status.textContent = ''; }, 3000);
    } else {
      status.textContent = '✗ 更新失敗';
      status.style.color = '#dc2626';
    }
  } catch {
    status.textContent = '✗ 更新失敗';
    status.style.color = '#dc2626';
  }
  btn.disabled = false;
  btn.textContent = '↺ 更新投影片圖片';
}

function reloadImages() {
  imageVersion = Date.now();
  document.querySelectorAll('.thumb img').forEach(img => {
    const base = img.src.split('?')[0];
    img.src = base + '?v=' + imageVersion;
  });
  const mainImg = document.querySelector('.slide-image-wrap img');
  if (mainImg) {
    const base = mainImg.src.split('?')[0];
    mainImg.src = base + '?v=' + imageVersion;
  }
}

async function loadSlides() {
  const res = await fetch('/api/slides');
  const data = await res.json();
  slides = data.slides;
  document.getElementById('dirPath').textContent = data.dir;
  initTheme(data.theme || 'tech-dark');
  renderSidebar();
  if (slides.length > 0) selectSlide(0);
}

function renderSidebar() {
  const sb = document.getElementById('sidebar');
  sb.innerHTML = slides.map((s, i) => `
    <div class="thumb ${i === currentIdx ? 'active' : ''}" onclick="selectSlide(${i})" id="thumb-${i}">
      <img src="/api/slide/${s.idx}/image?v=${imageVersion}" loading="lazy" />
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
      <img src="/api/slide/${s.idx}/image?v=${imageVersion}" alt="第 ${s.idx} 頁" />
    </div>
    <div class="narration-section">
      <div class="narration-label">第 ${s.idx} 頁旁白</div>
      <textarea id="narration" oninput="onTextChange(${i})">${escapeHtml(s.narration || '')}</textarea>
      <div class="toolbar">
        <button class="btn-save" id="saveBtn" onclick="saveFromBtn('${s.idx}', ${i})">儲存</button>
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

function toggleSettings() {
  const panel = document.getElementById('settingsPanel');
  const btn = document.getElementById('settingsBtn');
  const visible = panel.style.display !== 'none';
  panel.style.display = visible ? 'none' : 'flex';
  btn.classList.toggle('active', !visible);
}

function onTtsChange() {
  const tts = document.getElementById('settingTts').value;
  document.getElementById('voiceGroup').style.display =
    (tts === 'edge' || tts === 'azure') ? 'flex' : 'none';
  document.getElementById('azureKeyGroup').style.display =
    tts === 'azure' ? 'flex' : 'none';
  document.getElementById('azureRegionGroup').style.display =
    tts === 'azure' ? 'flex' : 'none';
  if (tts === 'edge') document.getElementById('settingVoice').value = 'zh-TW-HsiaoChenNeural';
}

function getSettings() {
  const tts = document.getElementById('settingTts').value;
  const params = { tts, rate: document.getElementById('settingRate').value || '+0%' };
  if (tts === 'edge') {
    params.voice = document.getElementById('settingVoice').value;
  } else if (tts === 'azure') {
    params.voice = document.getElementById('settingVoice').value;
    params.azure_key = document.getElementById('settingAzureKey').value;
    params.azure_region = document.getElementById('settingAzureRegion').value;
  }
  return params;
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
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getSettings()),
    });
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

    def _read_theme(self) -> str:
        slides_md = self.output_dir / "slides.md"
        if slides_md.exists():
            m = re.search(r'^theme:\s*(\S+)', slides_md.read_text(encoding="utf-8"), re.MULTILINE)
            if m:
                return m.group(1)
        return "tech-dark"

    def _write_theme(self, theme: str) -> None:
        slides_md = self.output_dir / "slides.md"
        content = slides_md.read_text(encoding="utf-8")
        new_content = re.sub(r'^theme:\s*\S+', f'theme: {theme}', content, flags=re.MULTILINE)
        slides_md.write_text(new_content, encoding="utf-8")

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
            self.send_json({"dir": str(self.output_dir), "slides": slides,
                            "theme": self._read_theme()})

        elif path == "/api/theme":
            self.send_json({"theme": self._read_theme()})

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

        if path == "/api/theme":
            try:
                theme = json.loads(body).get("theme", "tech-dark")
                self._write_theme(theme)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)

        elif path.startswith("/api/slide/") and path.endswith("/narration"):
            idx = path.split("/")[3]
            try:
                text = json.loads(body).get("text", "")
                nf = self.output_dir / f"narration_{idx}.txt"
                nf.write_text(text + "\n", encoding="utf-8")
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/refresh-slides":
            try:
                cmd = [sys.executable, str(MAKE_VIDEO_PY), str(self.output_dir), "--marp-only"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    self.send_json({"ok": True})
                else:
                    err = (result.stderr.strip().splitlines() or ["未知錯誤"])[-1]
                    self.send_json({"ok": False, "error": err}, status=500)
            except subprocess.TimeoutExpired:
                self.send_json({"ok": False, "error": "逾時"}, status=500)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/generate":
            try:
                params = json.loads(body) if body else {}
                tts = params.get("tts", "edge")
                rate = params.get("rate", "+0%")
                cmd = [sys.executable, str(MAKE_VIDEO_PY), str(self.output_dir),
                       "--tts", tts, "--rate", rate]
                if tts == "edge":
                    voice = params.get("voice", "")
                    if voice:
                        cmd += ["--voice", voice]
                elif tts == "azure":
                    if params.get("azure_key"):
                        cmd += ["--azure-key", params["azure_key"]]
                    if params.get("azure_region"):
                        cmd += ["--azure-region", params["azure_region"]]
                    if params.get("voice"):
                        cmd += ["--azure-voice", params["voice"]]
                result = subprocess.run(
                    cmd,
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
