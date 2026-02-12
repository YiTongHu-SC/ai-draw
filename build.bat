@echo off
REM Build script for Windows

echo Building ai-draw for Windows...
pipenv run python build.py
pause
