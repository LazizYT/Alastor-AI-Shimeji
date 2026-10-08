@echo off
cd /d "%~dp0"

REM 1. If Alastor.exe exists, launch it directly
if exist "%~dp0Alastor.exe" (
    start "" "%~dp0Alastor.exe"
    exit
)

REM 2. If venv exists, use it
if exist "C:\Users\Laziko\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe" (
    start "" "C:\Users\Laziko\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe" "%~dp0PinkChan.pyw"
    exit
)

REM 3. Fallback to system pythonw
start "" pythonw "%~dp0PinkChan.pyw"
exit
