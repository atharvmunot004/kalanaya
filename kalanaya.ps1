# Kalanaya wrapper script for Windows PowerShell
# This allows running 'kalanaya' from anywhere

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the project directory
Set-Location $ScriptDir

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Run the main application
python -m src.main $args

