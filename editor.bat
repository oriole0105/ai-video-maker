@echo off
REM editor.bat — 開啟網頁版旁白編輯器
REM
REM 用法：
REM   雙擊執行              → 使用 example\ 資料夾（示範用）
REM   拖曳資料夾到此檔案    → 使用該資料夾

setlocal
set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    set "TARGET=%SCRIPT_DIR%example"
) else (
    set "TARGET=%~1"
)

python "%SCRIPT_DIR%narration_editor.py" "%TARGET%"
if errorlevel 1 pause
