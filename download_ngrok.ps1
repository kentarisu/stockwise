# PowerShell script to download and setup ngrok
Write-Host "Setting up ngrok for StockWise..." -ForegroundColor Green

# Create ngrok directory
if (!(Test-Path "C:\ngrok")) {
    New-Item -ItemType Directory -Path "C:\ngrok" -Force
    Write-Host "Created C:\ngrok directory" -ForegroundColor Yellow
}

# Download ngrok
Write-Host "Downloading ngrok..." -ForegroundColor Yellow
try {
    $url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $output = "C:\ngrok\ngrok.zip"
    
    # Use .NET WebClient to bypass SSL issues
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($url, $output)
    
    Write-Host "Downloaded ngrok successfully!" -ForegroundColor Green
    
    # Extract ngrok
    Write-Host "Extracting ngrok..." -ForegroundColor Yellow
    Expand-Archive -Path $output -DestinationPath "C:\ngrok" -Force
    Remove-Item $output -Force
    
    Write-Host "ngrok extracted successfully!" -ForegroundColor Green
    Write-Host "ngrok.exe is now available at C:\ngrok\ngrok.exe" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error downloading ngrok: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please download manually from: https://ngrok.com/download" -ForegroundColor Yellow
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://ngrok.com/ and create a free account" -ForegroundColor White
Write-Host "2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
Write-Host "3. Run: C:\ngrok\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN" -ForegroundColor White
Write-Host "4. Then run the start_ngrok.bat file to start the tunnel" -ForegroundColor White

