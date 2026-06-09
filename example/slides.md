---
marp: true
theme: default
paginate: true
style: |
  section {
    background: #1e2a38;
    color: #e0e0e0;
    font-family: "PingFang TC", "Microsoft JhengHei", sans-serif;
    font-size: 28px;
    padding: 50px 70px;
  }
  h1 { color: #4fc3f7; border-bottom: 2px solid #4fc3f7; padding-bottom: 10px; }
  strong { color: #ffcc02; }
  code { background: #0d1b2a; color: #80cbc4; border-radius: 4px; padding: 2px 8px; }
  pre { background: #0d1b2a; border-radius: 8px; padding: 20px; }
  pre code { color: #a5d6a7; background: transparent; font-size: 0.85em; }
---

# ai-video-maker 使用範例

## 歡迎使用自動化教學影片工具

這是一個展示用的投影片，搭配旁白文字，透過工具自動生成語音和影片。

---

# 工具的運作方式

1. 用 **Markdown** 撰寫投影片內容
2. 用純文字撰寫每頁的**口說旁白**
3. 執行一行指令，自動產生完整影片

```bash
python make_video.py ./example/
```

**輸出：** `example/final.mp4`（Full HD，含字幕）

---

# 開始製作你的第一部影片

將 `example/` 資料夾複製一份，修改投影片和旁白內容，就能做出專屬的教學影片。

**旁白撰寫提示：**

- 用自然的口語，不用念程式碼指令
- 全部用中文，避免中英文切換
- 每頁旁白約 100–200 字最適合
