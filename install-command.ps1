# PowerShell script to add kalanaya to PATH
# Run this script to make kalanaya available from anywhere

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvScripts = Join-Path $ProjectRoot "venv\Scripts"

Write-Host "Installing kalanaya command..." -ForegroundColor Green

# Check if venv exists
if (-not (Test-Path $VenvScripts)) {
    Write-Host "Error: Virtual environment not found at $VenvScripts" -ForegroundColor Red
    Write-Host "Please create a virtual environment first." -ForegroundColor Yellow
    exit 1
}

# Check if kalanaya.exe exists
$KalanayaExe = Join-Path $VenvScripts "kalanaya.exe"
if (-not (Test-Path $KalanayaExe)) {
    Write-Host "Error: kalanaya.exe not found. Installing package..." -ForegroundColor Yellow
    & "$VenvScripts\python.exe" -m pip install -e $ProjectRoot
}

# Get current user PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if already in PATH
if ($CurrentPath -notlike "*$VenvScripts*") {
    # Add to user PATH
    [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$VenvScripts", "User")
    Write-Host "Added $VenvScripts to your user PATH" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Please close and reopen your terminal for changes to take effect." -ForegroundColor Yellow
    Write-Host "After reopening, you can run 'kalanaya' from anywhere!" -ForegroundColor Green
} else {
    Write-Host "kalanaya is already in your PATH!" -ForegroundColor Green
}

Write-Host ""
Write-Host "To test, close this terminal and open a new one, then run: kalanaya" -ForegroundColor Cyan

