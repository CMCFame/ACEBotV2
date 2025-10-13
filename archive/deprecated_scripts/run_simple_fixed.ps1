# run_simple_fixed.ps1
# Simple script to run the ACE app

Write-Host "=" * 50 -ForegroundColor Green
Write-Host "Simple ACE Questionnaire App" -ForegroundColor Green  
Write-Host "=" * 50 -ForegroundColor Green

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install streamlit boto3

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
$awsKey = $env:AWS_ACCESS_KEY_ID
$awsSecret = $env:AWS_SECRET_ACCESS_KEY

if ($awsKey -and $awsSecret) {
    Write-Host "✓ AWS credentials found in environment" -ForegroundColor Green
} else {
    Write-Host "⚠️  AWS credentials not found in environment" -ForegroundColor Yellow
    Write-Host "They might be in .streamlit/secrets.toml (that's fine too)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starting Simple ACE App..." -ForegroundColor Green
Write-Host "Open: http://localhost:8520" -ForegroundColor White
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start the app
python -m streamlit run simple_ace_app.py --server.port 8520 --server.address localhost