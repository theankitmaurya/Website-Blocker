@echo off
cd /d "%~dp0"
if exist "dist\WebsiteBlocker.exe" (
    start "" "dist\WebsiteBlocker.exe"
) else (
    start "" pythonw run.py
)
