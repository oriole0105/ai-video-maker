@echo off
REM generate.bat — 生成教學影片（完整流程：投影片→語音→影片→字幕）
REM
REM 用法：
REM   雙擊執行              → 使用 example\ 資料夾（示範用）
REM   拖曳資料夾到此檔案    → 使用該資料夾
REM   generate.bat my_lesson\ --rate "+20%"

setlocal
set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    set "TARGET=%SCRIPT_DIR%example"
) else (
    set "TARGET=%~1"
    shift
)

python "%SCRIPT_DIR%make_video.py" "%TARGET%" %*
if errorlevel 1 pause
