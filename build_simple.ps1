# Simple Windows build script for headless_ultrasonic
# Fixed encoding issues and simplified for direct execution

$ErrorActionPreference = "Stop"

Write-Host "Starting headless_ultrasonic Windows build..." -ForegroundColor Green

# Detect architecture
$arch = $env:PROCESSOR_ARCHITECTURE
switch ($arch) {
    "AMD64" { $targetArch = "amd64" }
    "ARM64" { $targetArch = "arm64" }
    "x86"   { $targetArch = "x86" }
    default {
        Write-Host "Unsupported architecture: $arch" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Detected architecture: $arch -> $targetArch" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "Error: main.py not found. Please run from headless_ultrasonic directory" -ForegroundColor Red
    exit 1
}

# Check Python
try {
    python --version
    Write-Host "Python detected" -ForegroundColor Green
} catch {
    Write-Host "Python not found" -ForegroundColor Red
    exit 1
}

# Install/check dependencies
Write-Host "Installing dependencies using Tsinghua mirror..." -ForegroundColor Cyan
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "numpy<2.0" "scipy>=1.11.0" sounddevice fastapi uvicorn pydantic watchfiles pyinstaller

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Set output file
$outputFile = "dist\headless_ultrasonic_windows_${targetArch}_onefile.exe"

# Clean previous build
if (Test-Path $outputFile) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item $outputFile -Force
}

if (Test-Path "*.spec") {
    Remove-Item "*.spec" -Force
}

# Build
Write-Host "Starting PyInstaller build ($targetArch)..." -ForegroundColor Cyan

$pyinstallerArgs = @(
    "--onefile"
    "--collect-all", "scipy"
    "--collect-all", "numpy"
    "--hidden-import", "sounddevice"
    "--hidden-import", "watchfiles"
    "--hidden-import", "uvicorn.main"
    "--add-data", "config.json;."
    "--add-data", "config_loader.py;."
    "--add-data", "core;core"
    "--add-data", "models;models"
    "--add-data", "api;api"
    "--distpath", "dist"
    "--workpath", "build_onefile_$targetArch"
    "--name", "headless_ultrasonic_windows_${targetArch}_onefile"
    "--console"
    "main.py"
)

python -m PyInstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Check result
if (Test-Path $outputFile) {
    $fileSize = (Get-Item $outputFile).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)

    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Output file: $outputFile" -ForegroundColor Cyan
    Write-Host "File size: $fileSizeMB MB" -ForegroundColor Cyan
    Write-Host "Architecture: $targetArch" -ForegroundColor Cyan
} else {
    Write-Host "Build failed - output file not found" -ForegroundColor Red
    exit 1
}

Write-Host "Windows build completed successfully!" -ForegroundColor Green