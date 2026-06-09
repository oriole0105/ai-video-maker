# ai-video-maker

用 Markdown 寫投影片、用文字寫旁白，一鍵自動產生有語音旁白和字幕的教學影片。

```
slides.md（投影片）+ narration_01.txt…（旁白）
         ↓  雙擊 step1_generate
         final.mp4（Full HD，含字幕軌）
```

> `example/` 資料夾內附有完整的 11 頁示範，雙擊腳本即可試用。

---

## 快速上手：三個腳本

安裝完成後，只需要這三個腳本，不需要打任何指令。

### step1\_generate — 生成影片

將投影片和旁白合成為完整的 MP4 影片。

| 平台 | 操作 |
|------|------|
| **Mac** | 終端機執行 `./step1_generate.sh` |
| **Windows** | 雙擊 `step1_generate.bat` |
| 指定資料夾 | 將資料夾拖曳到腳本圖示上 |

```bash
# 不指定資料夾時，預設使用 example/
./step1_generate.sh

# 指定自己的資料夾
./step1_generate.sh ./my_lesson/

# 加快語速
./step1_generate.sh ./my_lesson/ --rate "+20%"
```

### step2\_editor — 旁白編輯器

開啟網頁版編輯器，側邊欄顯示所有投影片縮圖，右側可直接編輯旁白文字。

| 平台 | 操作 |
|------|------|
| **Mac** | 終端機執行 `./step2_editor.sh` |
| **Windows** | 雙擊 `step2_editor.bat` |
| 指定資料夾 | 將資料夾拖曳到腳本圖示上 |

```bash
./step2_editor.sh ./my_lesson/
# 自動開啟 http://127.0.0.1:8765
```

| 功能 | 說明 |
|------|------|
| 左側縮圖欄 | 所有投影片縮圖，點擊切換頁面 |
| 右側主畫面 | 投影片大圖 + 旁白文字框 |
| Cmd / Ctrl + S | 儲存目前頁旁白 |
| 方向鍵 ← → | 切換投影片（焦點不在文字框時）|
| ▶ 生成影片 | 儲存所有旁白並直接產生影片 |

> 需先執行過 `step1_generate` 才有投影片圖片可顯示。

### step3\_concat — 重新合併

修改個別片段後，跳過語音合成，直接將現有片段重新合成為最終影片。

| 平台 | 操作 |
|------|------|
| **Mac** | 終端機執行 `./step3_concat.sh` |
| **Windows** | 雙擊 `step3_concat.bat` |

```bash
./step3_concat.sh ./my_lesson/
```

**使用時機：** 執行 `step1_generate` 之後，若只修改了投影片 CSS 樣式或重建了個別片段，用此腳本快速重新合成，不需重新跑語音合成。

---

## 建議工作流程

```
第一次使用
    ↓
step1_generate（產生影片，同時產出投影片圖片）
    ↓
step2_editor（用網頁編輯器調整旁白）
    ↓  在編輯器內點「▶ 生成影片」重新產生
    ↓  或
step3_concat（只重新合成，不重跑語音）
```

---

## 系統需求

| 工具 | 說明 | 安裝方式 |
|------|------|---------|
| Python 3.10+ | 主程式 | [python.org](https://www.python.org/) |
| uv | Python 套件管理 | 見下方 |
| FFmpeg | 影片處理 | Mac: `brew install ffmpeg` / Win: `winget install ffmpeg` |
| Node.js + Marp CLI | 投影片轉圖片 | `npm install -g @marp-team/marp-cli` |
| Google Chrome | Marp 渲染引擎 | `brew install --cask google-chrome` |

---

## 安裝步驟

### 1. 安裝 uv

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

### 3. 下載並安裝

```bash
git clone https://github.com/oriole0105/ai-video-maker
cd ai-video-maker
python setup.py
```

安裝腳本會自動在 `venv/` 目錄下建立虛擬環境，安裝語音合成（edge-tts）與字幕辨識（whisper）套件。

### 4. 確認安裝

```bash
python setup.py --check
```

---

## 準備你的影片資料夾

```
my_lesson/
├── slides.md          ← Marp 投影片
├── narration_01.txt   ← 第一頁旁白
├── narration_02.txt   ← 第二頁旁白
└── narration_03.txt   ← 第三頁旁白（頁數須與投影片相符）
```

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

三條橫線 `---` 即為分頁，其餘為標準 Markdown 語法。

### 撰寫旁白

每頁一個純文字檔，用自然的口語撰寫。語音合成使用**微軟台灣腔中文女聲**（免費）。

**旁白注意事項：**
- 旁白請全用中文，避免中英文混用（會造成語音停頓）
- 若需念英文縮寫，字母之間加空格：`G B` 而非 `GB`
- 多音字念錯時，改用同義詞替換（例：「重新執行」取代「重跑」）

### 執行結果

```
my_lesson/
├── slides.001.png     ← 投影片圖片
├── audio_01.mp3       ← 語音
├── segment_01.mp4     ← 單頁片段
│   ...
├── final.srt          ← 字幕（Whisper 語音辨識）
└── final.mp4          ← ✅ 完整影片（1920×1080，含字幕軌）
```

---

## 可用語音

| 語音 ID | 說明 |
|---------|------|
| `zh-TW-HsiaoChenNeural` | 女聲（預設）|
| `zh-TW-YunJheNeural` | 男聲 |
| `zh-TW-HsiaoYuNeural` | 女聲（另一版本）|

```bash
./step1_generate.sh ./my_lesson/ --voice zh-TW-YunJheNeural
```

---

## 注意事項

- 字幕辨識首次執行需下載 Whisper 模型（約 1 GB），之後不需重複下載
- 未安裝 Whisper 時，工具會自動跳過字幕步驟
- 投影片頁數與旁白檔案數量必須相符

---

## 授權

MIT License
