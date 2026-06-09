# ai-video-maker

用 Markdown 寫投影片、用文字寫旁白，一行指令自動產生有語音旁白和字幕的教學影片。

```
投影片（slides.md）+ 旁白（narration_01.txt…）
         ↓  python make_video.py ./my_lesson/
         final.mp4（Full HD，含字幕軌）
```

## 系統需求

| 工具 | 說明 | 安裝方式 |
|------|------|---------|
| Python 3.10+ | 主程式 | [python.org](https://www.python.org/) |
| uv | Python 套件管理 | 見下方 |
| FFmpeg | 影片處理 | Mac: `brew install ffmpeg` / Win: `winget install ffmpeg` |
| Node.js + Marp CLI | 投影片轉圖片 | `npm install -g @marp-team/marp-cli` |
| Google Chrome | Marp 渲染引擎 | `brew install --cask google-chrome` |

## 安裝步驟

### 1. 安裝 uv（Python 套件管理）

```bash
# macOS / Linux
curl -Ls https://astral.sh/uv/install.sh | sh

# Windows（PowerShell）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安裝系統工具

**macOS：**
```bash
brew install ffmpeg node
brew install --cask google-chrome
npm install -g @marp-team/marp-cli
```

**Windows（以系統管理員執行 PowerShell）：**
```powershell
winget install ffmpeg
winget install OpenJS.NodeJS
winget install Google.Chrome
npm install -g @marp-team/marp-cli
```

### 3. 下載並安裝 ai-video-maker

```bash
git clone <repo-url>
cd ai-video-maker
python setup.py
```

安裝腳本會在 `venv/` 目錄下建立 Python 虛擬環境，並自動安裝語音合成（edge-tts）和字幕辨識（whisper）套件。

### 4. 確認安裝成功

```bash
python setup.py --check
```

## 使用方式

### 準備影片目錄

```
my_lesson/
├── slides.md          ← Marp 投影片（必要）
├── narration_01.txt   ← 第一頁旁白（必要）
├── narration_02.txt   ← 第二頁旁白
└── narration_03.txt   ← 第三頁旁白
```

> 旁白數量必須和投影片頁數相符。

### 撰寫投影片（slides.md）

```markdown
---
marp: true
theme: default
---

# 第一頁標題

- 重點一
- 重點二

---

# 第二頁標題

內容文字
```

### 撰寫旁白（narration_01.txt）

每一頁旁白是一個純文字檔，用自然的口語寫，不要放英文術語。
語音合成使用**微軟台灣腔中文女聲**，免費、發音自然。

### 產生影片

```bash
python make_video.py ./my_lesson/
```

**選項：**
```bash
python make_video.py --voice zh-TW-YunJheNeural ./my_lesson/   # 換聲音（男聲）
python make_video.py --rate "+20%" ./my_lesson/                # 加快語速
```

**可用台灣腔聲音：**
- `zh-TW-HsiaoChenNeural`（預設，女聲）
- `zh-TW-YunJheNeural`（男聲）
- `zh-TW-HsiaoYuNeural`（女聲，另一個版本）

### 執行結果

```
my_lesson/
├── slides.001.png     ← 投影片圖片
├── audio_01.mp3       ← 語音
├── segment_01.mp4     ← 單頁片段
│   ...
├── final.srt          ← 字幕（Whisper 自動辨識）
└── final.mp4          ← ✅ 最終影片（含字幕軌，1920×1080）
```

## 旁白編輯器（網頁介面）

不想開多個文字檔，可以用瀏覽器編輯器同時瀏覽投影片和旁白：

```bash
python narration_editor.py ./my_lesson/
# 自動開啟 http://127.0.0.1:8765
```

| 功能 | 說明 |
|------|------|
| 左側縮圖欄 | 所有投影片縮圖，點擊切換 |
| 右側主畫面 | 投影片大圖 + 旁白文字框 |
| Cmd/Ctrl + S | 儲存目前頁旁白 |
| 方向鍵 ← → | 切換投影片（焦點不在文字框時）|
| ▶ 生成影片 | 儲存所有旁白並呼叫 make_video.py |

> 投影片圖片需先存在（執行過一次 `make_video.py` 或 `marp slides.md --images png`）

## 試用範例

```bash
python make_video.py ./example/
```

## 注意事項

- **旁白請全用中文**，盡量不要中英文混用，這樣語音合成效果最好
- 字幕是用語音辨識自動產生，首次執行需下載 Whisper 模型（約 1–1.5 GB）
- 如果不需要字幕，Whisper 未安裝時工具會自動跳過字幕步驟

## 授權

MIT License
