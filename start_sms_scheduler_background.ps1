# StockWise SMS Scheduler - Run in Background
# This script runs the SMS scheduler as a background process

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting StockWise SMS Scheduler in background..." -ForegroundColor Green
Write-Host ""
Write-Host "This scheduler will automatically send:" -ForegroundColor Cyan
Write-Host "  - Daily Sales Summary at 8:00 PM" -ForegroundColor White
Write-Host "  - Low Stock Alerts IMMEDIATELY when stock drops (real-time)" -ForegroundColor Yellow
Write-Host "  - Pricing Recommendations at 10:00 AM (every 3 days)" -ForegroundColor White
Write-Host ""

# Check if scheduler is already running
$existing = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*sms_scheduler.py*"
}

if ($existing) {
    Write-Host "SMS Scheduler is already running (PID: $($existing.Id))" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to restart it? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Stopping existing scheduler..." -ForegroundColor Yellow
        Stop-Process -Id $existing.Id -Force
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Keeping existing scheduler running." -ForegroundColor Green
        exit
    }
}

# Activate virtual environment and start scheduler
$pythonPath = Join-Path $scriptPath "venv\Scripts\python.exe"
$schedulerPath = Join-Path $scriptPath "sms_scheduler.py"

# Start the scheduler in a hidden window
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = $pythonPath
$processInfo.Arguments = $schedulerPath
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.RedirectStandardOutput = $false
$processInfo.RedirectStandardError = $false
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

Write-Host ""
Write-Host "SMS Scheduler started successfully!" -ForegroundColor Green
Write-Host "Process ID: $($process.Id)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To check logs, run:" -ForegroundColor Yellow
Write-Host "  Get-Content sms_scheduler.log -Wait" -ForegroundColor White
Write-Host ""
Write-Host "To stop the scheduler, run:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id $($process.Id)" -ForegroundColor White
Write-Host "  Or use: .\stop_sms_scheduler.ps1" -ForegroundColor White
Write-Host ""

# Save PID to file for easy stopping later
$process.Id | Out-File -FilePath "sms_scheduler.pid" -Encoding ASCII

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

