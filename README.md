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
theme: tech-dark
---

# 第一頁標題

- 重點一
- 重點二

---

# 第二頁標題

內容文字
```

三條橫線 `---` 即為分頁，其餘為標準 Markdown 語法。

> **注意：** `---` 前後必須各留一行空行，否則 Markdown 會把它解析成「把上一行變成標題」，導致兩頁合併成一頁。
>
> ```markdown
> 這是上一頁的最後一行            ← 錯誤：緊接著 ---，這行會變成標題
> ---
>
> 這是上一頁的最後一行            ← 正確：空行後才是分頁線
>
> ---
> ```

### 切換主題

工具內建 4 套視覺主題，修改 `slides.md` 第一行的 `theme:` 欄位即可切換：

| 主題名稱 | 風格 | 適合場合 |
|---------|------|---------|
| `tech-dark` | 深藍科技風（預設）| 技術簡報、深色場地 |
| `clean-light` | 白底清爽風 | 明亮場地、一般簡報 |
| `corporate-navy` | 藍灰商務風 | 正式會議、企業場合 |
| `warm-amber` | 暖琥珀深色風 | 創意分享、視覺鮮明 |

也可以用腳本直接切換：

```bash
# macOS
./set_theme.sh clean-light ./my_lesson/

# Windows（雙擊後輸入，或在命令提示字元）
set_theme.bat clean-light my_lesson\
```

不帶任何參數執行可查看所有可用主題。

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
├── slides.pdf         ← 投影片 PDF（供文件分享）
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

## 公司環境 / 離線安裝

若公司內網無法存取 PyPI 或 HuggingFace，可用離線包方式安裝。

### 步驟一：在家準備離線包（需要網路）

```bash
# 下載 Windows 套件 + Whisper 模型到 offline_pack/
python prepare_offline.py

# 指定 Python 版本（需與公司 Windows 機器一致）
python prepare_offline.py --py 311
```

完成後將整個 `ai-video-maker/` 資料夾壓縮傳給同仁（含 `offline_pack/`，約 2 GB）。

### 步驟二：在公司 Windows 安裝（不需網路）

雙擊 `setup_offline.bat`，腳本會自動：
- 建立 Python 虛擬環境
- 從 `offline_pack/wheels/` 安裝套件（不碰 PyPI）
- 使用 `offline_pack/whisper_model/` 的本機模型（不碰 HuggingFace）

### 網路需求說明

| 元件 | 需要網路 | 說明 |
|------|---------|------|
| 套件安裝 | ❌ 離線 | 從 offline_pack/wheels/ 安裝 |
| Whisper 模型 | ❌ 離線 | 從 offline_pack/whisper_model/ 載入 |
| Marp / FFmpeg | ❌ 離線 | 本機工具 |
| Edge TTS 語音合成 | ✅ 需要 | 呼叫 `*.tts.speech.microsoft.com`（Microsoft 官方服務，大多公司網路可通）|

---

## 注意事項

- 字幕辨識首次執行需下載 Whisper 模型（約 1 GB），之後不需重複下載
- 未安裝 Whisper 時，工具會自動跳過字幕步驟
- 投影片頁數與旁白檔案數量必須相符
- `slides.md` 的分頁線 `---` 前後必須各留一個空行，否則 Markdown 會把它解析為 setext 標題底線，導致兩頁合併成一頁、整體頁數與旁白對不上

---

## 授權

MIT License
