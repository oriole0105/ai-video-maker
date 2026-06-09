@echo off
REM concat.bat — 只合併現有片段（跳過 TTS，適合微調後重新合成）
REM
REM 使用時機：
REM   已經跑過 generate.bat，只修改了少數片段，不想重新跑語音合成
REM
REM 用法：
REM   雙擊執行              → 使用 example\ 資料夾
REM   拖曳資料夾到此檔案    → 使用該資料夾

setlocal
set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    set "TARGET=%SCRIPT_DIR%example"
) else (
    set "TARGET=%~1"
)

python "%SCRIPT_DIR%make_video.py" --concat-only "%TARGET%"
if errorlevel 1 pause
