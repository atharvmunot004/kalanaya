@echo off
REM Batch script to add kalanaya to PATH
REM Run this script to make kalanaya available from anywhere

setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_SCRIPTS=%PROJECT_ROOT%venv\Scripts"

echo Installing kalanaya command...

REM Check if venv exists
if not exist "%VENV_SCRIPTS%" (
    echo Error: Virtual environment not found at %VENV_SCRIPTS%
    echo Please create a virtual environment first.
    exit /b 1
)

REM Check if kalanaya.exe exists
if not exist "%VENV_SCRIPTS%\kalanaya.exe" (
    echo Error: kalanaya.exe not found. Installing package...
    "%VENV_SCRIPTS%\python.exe" -m pip install -e "%PROJECT_ROOT%"
)

REM Get current user PATH
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CURRENT_PATH=%%B"

REM Check if already in PATH
echo %CURRENT_PATH% | findstr /C:"%VENV_SCRIPTS%" >nul
if errorlevel 1 (
    REM Add to user PATH
    setx PATH "%CURRENT_PATH%;%VENV_SCRIPTS%"
    echo Added %VENV_SCRIPTS% to your user PATH
    echo.
    echo IMPORTANT: Please close and reopen your terminal for changes to take effect.
    echo After reopening, you can run 'kalanaya' from anywhere!
) else (
    echo kalanaya is already in your PATH!
)

echo.
echo To test, close this terminal and open a new one, then run: kalanaya

endlocal

