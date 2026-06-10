@echo off
setlocal EnableDelayedExpansion
set SCRIPT_DIR=%~dp0

echo ================================================
echo   ai-video-maker 離線安裝
echo ================================================
echo.

:: ── 確認 Python ──────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python，請先安裝 Python 3.10+
    echo        https://www.python.org/downloads/
    echo        安裝時勾選 "Add Python to PATH"
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   Python: %%v

:: ── 確認離線包存在 ────────────────────────────────────────────────────────────
if not exist "%SCRIPT_DIR%offline_pack\wheels\" (
    echo.
    echo [錯誤] 找不到 offline_pack\wheels\
    echo        請先在有網路的電腦執行：
    echo          python prepare_offline.py
    echo        然後將整個 ai-video-maker\ 資料夾複製過來
    goto :fail
)

set VENV_DIR=%SCRIPT_DIR%venv
set WHEELS=%SCRIPT_DIR%offline_pack\wheels
echo   套件來源: %WHEELS%
echo   安裝位置: %VENV_DIR%
echo.

:: ── [ 1/3 ] Edge TTS ─────────────────────────────────────────────────────────
echo [ 1/3 ] 安裝 edge-tts...
python -m venv "%VENV_DIR%\tts"
if errorlevel 1 ( echo [錯誤] 建立 venv 失敗 & goto :fail )

"%VENV_DIR%\tts\Scripts\pip.exe" install ^
    --no-index --find-links "%WHEELS%" ^
    edge-tts --quiet
if errorlevel 1 ( echo [錯誤] edge-tts 安裝失敗 & goto :fail )
echo   OK

:: ── [ 2/3 ] Whisper ───────────────────────────────────────────────────────────
echo [ 2/3 ] 安裝 faster-whisper...
python -m venv "%VENV_DIR%\whisper"
if errorlevel 1 ( echo [錯誤] 建立 venv 失敗 & goto :fail )

"%VENV_DIR%\whisper\Scripts\pip.exe" install ^
    --no-index --find-links "%WHEELS%" ^
    faster-whisper opencc-python-reimplemented --quiet
if errorlevel 1 ( echo [錯誤] faster-whisper 安裝失敗 & goto :fail )
echo   OK

:: ── [ 3/3 ] Piper TTS ────────────────────────────────────────────────────────
echo [ 3/3 ] 安裝 piper-tts...
python -m venv "%VENV_DIR%\piper"
if errorlevel 1 ( echo [錯誤] 建立 venv 失敗 & goto :fail )

"%VENV_DIR%\piper\Scripts\pip.exe" install ^
    --no-index --find-links "%WHEELS%" ^
    piper-tts --quiet
if errorlevel 1 ( echo [錯誤] piper-tts 安裝失敗 & goto :fail )
echo   OK

:: ── 系統工具檢查 ──────────────────────────────────────────────────────────────
echo.
echo ── 系統工具檢查 ─────────────────────────────────
where ffmpeg >nul 2>&1
if errorlevel 1 ( echo   缺少 ffmpeg   ->  winget install ffmpeg
) else ( echo   OK  ffmpeg )

where node >nul 2>&1
if errorlevel 1 ( echo   缺少 node     ->  winget install OpenJS.NodeJS
) else ( echo   OK  node )

where marp >nul 2>&1
if errorlevel 1 ( echo   缺少 marp     ->  npm install -g @marp-team/marp-cli
) else ( echo   OK  marp )

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo   OK  Chrome
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo   OK  Chrome
) else (
    echo   缺少 Chrome  ->  winget install Google.Chrome
)

:: ── Whisper 模型狀態 ───────────────────────────────────────────────────────────
echo.
echo ── Whisper 模型 ─────────────────────────────────
if exist "%SCRIPT_DIR%offline_pack\whisper_model\model.bin" (
    echo   OK  本機模型（離線模式，不需下載）
) else (
    echo   ！  offline_pack\whisper_model\ 不存在或不完整
    echo       首次產生字幕時會嘗試從 HuggingFace 下載（約 1.5 GB）
    echo       若公司網路擋 HuggingFace，請先在家執行：
    echo         python prepare_offline.py --model-only
)

:: ── Piper 模型狀態 ─────────────────────────────────────────────────────────
echo.
echo ── Piper 模型 ───────────────────────────────────
if exist "%SCRIPT_DIR%offline_pack\piper_model\zh_CN-huayan-medium.onnx" (
    echo   OK  Piper 模型已就緒（--tts piper 可用）
) else (
    echo   ！  offline_pack\piper_model\ 不存在
    echo       如需使用 --tts piper，請先在家執行：
    echo         python prepare_offline.py --piper-only
)

:: ── 網路需求提醒 ────────────────────────────────────────────────────────────
echo.
echo ── 網路需求 ─────────────────────────────────────
echo   語音合成（Edge TTS）需連到 Microsoft 伺服器
echo   確認公司網路可存取：*.tts.speech.microsoft.com
echo   其餘功能（Marp、FFmpeg、Whisper）完全離線可用
echo.

echo ================================================
echo   安裝完成！
echo   雙擊 step1_generate.bat 開始製作影片
echo ================================================
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
