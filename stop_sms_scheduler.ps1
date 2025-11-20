# Stop StockWise SMS Scheduler

Write-Host "Stopping StockWise SMS Scheduler..." -ForegroundColor Yellow

# Check for PID file
$pidFile = "sms_scheduler.pid"
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile
    try {
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Write-Host "SMS Scheduler stopped (PID: $pid)" -ForegroundColor Green
        Remove-Item $pidFile
    } catch {
        Write-Host "Process not found or already stopped." -ForegroundColor Yellow
    }
} else {
    # Try to find by command line
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*sms_scheduler.py*"
    }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Stop-Process -Id $proc.Id -Force
            Write-Host "SMS Scheduler stopped (PID: $($proc.Id))" -ForegroundColor Green
        }
    } else {
        Write-Host "No SMS Scheduler process found running." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

