# StockFlow Setup Script for Windows PowerShell
# Run from the stockflow\ directory:
#   .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "`nStockFlow Setup Script" -ForegroundColor Cyan
Write-Host "======================`n" -ForegroundColor Cyan

# Check Python is available
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version

# Create a virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "`nVirtual environment already exists." -ForegroundColor Green
}

# Activate venv
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "`nInstalling requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run migrations
Write-Host "`nApplying database migrations..." -ForegroundColor Yellow
python manage.py migrate

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nTo start the development server, run:" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host "`nThen open: http://127.0.0.1:8000/signup/" -ForegroundColor Cyan
Write-Host ""
