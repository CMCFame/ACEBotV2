# run_simple.ps1
# Run the simple ACE app

Write-Host "=" * 50 -ForegroundColor Green
Write-Host "Simple ACE Questionnaire App" -ForegroundColor Green  
Write-Host "=" * 50 -ForegroundColor Green

# Check if Python and Streamlit are available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

try {
    python -c "import streamlit" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Streamlit is available" -ForegroundColor Green
    } else {
        throw "Streamlit not found"
    }
} catch {
    Write-Host "❌ Installing Streamlit..." -ForegroundColor Yellow
    python -m pip install streamlit boto3
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check AWS credentials
$awsKey = $env:AWS_ACCESS_KEY_ID
$awsSecret = $env:AWS_SECRET_ACCESS_KEY

if ($awsKey -and $awsSecret) {
    Write-Host "✓ AWS credentials found" -ForegroundColor Green
} else {
    Write-Host "⚠️  AWS credentials not set" -ForegroundColor Yellow
    Write-Host "Set them with:" -ForegroundColor Yellow
    Write-Host '$env:AWS_ACCESS_KEY_ID = "your_key"' -ForegroundColor Cyan
    Write-Host '$env:AWS_SECRET_ACCESS_KEY = "your_secret"' -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🚀 Starting Simple ACE App on port 8520..." -ForegroundColor Green
Write-Host "Open: http://localhost:8520" -ForegroundColor White
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

try {
    python -m streamlit run simple_ace_app.py --server.port 8520 --server.address localhost
} catch {
    Write-Host "❌ Error starting app: $_" -ForegroundColor Red
} finally {
    Write-Host "✓ App stopped" -ForegroundColor Green
}