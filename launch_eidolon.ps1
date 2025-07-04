# =======================
# Eidolon Auto-Launcher
# =======================

Set-Location -Path "E:\Eidolon"

Write-Host "🔹 Activating Eidolon Python 3.10 venv..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "🔹 Launching Eidolon..." -ForegroundColor Cyan
python -m eidolon.main

# Keep window open after exit
Write-Host "Eidolon closed. Press Enter to exit." -ForegroundColor Yellow
Read-Host
