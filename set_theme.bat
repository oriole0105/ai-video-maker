@echo off
setlocal
set SCRIPT_DIR=%~dp0

if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe
) else (
    set PYTHON=python
)

"%PYTHON%" "%SCRIPT_DIR%set_theme.py" %*

if errorlevel 1 (
    echo.
    pause
)
