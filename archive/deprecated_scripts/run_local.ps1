# run_local.ps1
# PowerShell script to run ACEBotV2 locally

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "ACEBotV2 Local Development Server" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check if Python is installed
if (-not (Test-Command "python")) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green

# Check if Streamlit is installed
try {
    $streamlitVersion = python -m streamlit version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Streamlit is installed" -ForegroundColor Green
    } else {
        throw "Streamlit not found"
    }
} catch {
    Write-Host "❌ Streamlit not installed. Installing..." -ForegroundColor Yellow
    python -m pip install streamlit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Streamlit" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Streamlit installed successfully" -ForegroundColor Green
}

# Check if boto3 is installed
try {
    python -c "import boto3; print('✓ Boto3 is available')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Boto3 not found"
    }
} catch {
    Write-Host "❌ Boto3 not installed. Installing..." -ForegroundColor Yellow
    python -m pip install boto3
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Boto3" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Boto3 installed successfully" -ForegroundColor Green
}

# Check for AWS credentials
Write-Host "`n" + "=" * 40 -ForegroundColor Cyan
Write-Host "AWS Credentials Check" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

$awsAccessKey = $env:AWS_ACCESS_KEY_ID
$awsSecretKey = $env:AWS_SECRET_ACCESS_KEY

if ($awsAccessKey -and $awsSecretKey) {
    Write-Host "✓ AWS credentials found in environment variables" -ForegroundColor Green
} else {
    Write-Host "⚠️  AWS credentials not found in environment variables" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set AWS credentials for this session, run:" -ForegroundColor Yellow
    Write-Host '$env:AWS_ACCESS_KEY_ID = "your_access_key_here"' -ForegroundColor Cyan
    Write-Host '$env:AWS_SECRET_ACCESS_KEY = "your_secret_key_here"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or create a .env file in this directory with:" -ForegroundColor Yellow
    Write-Host "AWS_ACCESS_KEY_ID=your_access_key_here" -ForegroundColor Cyan
    Write-Host "AWS_SECRET_ACCESS_KEY=your_secret_key_here" -ForegroundColor Cyan
    Write-Host ""
}

# Set the port (higher than 8506 as requested)
$port = 8510

# Check if port is available
try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
    $listener.Start()
    $listener.Stop()
    Write-Host "✓ Port $port is available" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Port $port might be in use. Streamlit will find an alternative." -ForegroundColor Yellow
}

# Display startup information
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "Starting ACEBotV2 Development Server" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Port: $port" -ForegroundColor White
Write-Host "URL: http://localhost:$port" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Green

# Check if app.py exists
if (-not (Test-Path "app.py")) {
    Write-Host "❌ app.py not found in current directory" -ForegroundColor Red
    Write-Host "Make sure you're running this script from the ACEBotV2 project root" -ForegroundColor Red
    exit 1
}

# Start Streamlit with specified port
try {
    python -m streamlit run app.py --server.port $port --server.address localhost --server.headless false
} catch {
    Write-Host "`n❌ Error starting Streamlit server" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    Write-Host "`n✓ Streamlit server stopped" -ForegroundColor Green
}

Write-Host "`nThank you for using ACEBotV2!" -ForegroundColor Green