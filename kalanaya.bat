@echo off
REM Kalanaya wrapper script for Windows Command Prompt
REM This allows running 'kalanaya' from anywhere

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to the project directory
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the main application
python -m src.main %*

