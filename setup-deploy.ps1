# Automated Deployment Setup Script
# Run this in PowerShell to set up your app automatically

Write-Host "🚀 Setting up automated deployment..." -ForegroundColor Green

# Check if Railway CLI is installed
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue

if (-not $railwayInstalled) {
    Write-Host "📦 Installing Railway CLI..." -ForegroundColor Yellow
    iwr https://railway.app/install.ps1 -useb | iex
    Write-Host "✅ Railway CLI installed!" -ForegroundColor Green
} else {
    Write-Host "✅ Railway CLI already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔐 Next steps (manual):" -ForegroundColor Cyan
Write-Host "1. Run: railway login" -ForegroundColor White
Write-Host "2. Run: railway init" -ForegroundColor White
Write-Host "3. Run: railway up" -ForegroundColor White
Write-Host ""
Write-Host "Your app will be deployed automatically!" -ForegroundColor Green
