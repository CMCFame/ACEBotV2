# setup_local.ps1
# PowerShell script to setup ACEBotV2 for local development

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "ACEBotV2 Local Development Setup" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check if Python is installed
if (-not (Test-Command "python")) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green

# Check if pip is available
if (-not (Test-Command "pip")) {
    Write-Host "❌ pip not found. Please install pip" -ForegroundColor Red
    exit 1
}

Write-Host "✓ pip is available" -ForegroundColor Green

# Install requirements
Write-Host "`n" + "=" * 40 -ForegroundColor Cyan
Write-Host "Installing Python Dependencies" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

if (Test-Path "requirements.txt") {
    Write-Host "Installing from requirements.txt..." -ForegroundColor White
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Requirements installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install some requirements" -ForegroundColor Red
    }
} else {
    Write-Host "No requirements.txt found. Installing basic requirements..." -ForegroundColor Yellow
    
    $basicRequirements = @("streamlit", "boto3", "pandas")
    
    foreach ($req in $basicRequirements) {
        Write-Host "Installing $req..." -ForegroundColor White
        python -m pip install $req
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Installed $req" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to install $req" -ForegroundColor Red
        }
    }
}

# AWS Credentials Setup
Write-Host "`n" + "=" * 40 -ForegroundColor Cyan
Write-Host "AWS Credentials Setup" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

$awsAccessKey = $env:AWS_ACCESS_KEY_ID
$awsSecretKey = $env:AWS_SECRET_ACCESS_KEY

if (-not $awsAccessKey -or -not $awsSecretKey) {
    Write-Host "⚠️  AWS credentials not found in environment variables" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set AWS credentials, choose one of these methods:" -ForegroundColor White
    Write-Host ""
    Write-Host "Method 1 - Environment Variables (current session):" -ForegroundColor Yellow
    Write-Host '$env:AWS_ACCESS_KEY_ID = "your_access_key_here"' -ForegroundColor Cyan
    Write-Host '$env:AWS_SECRET_ACCESS_KEY = "your_secret_key_here"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Method 2 - Persistent Environment Variables:" -ForegroundColor Yellow
    Write-Host '[System.Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", "your_key", "User")' -ForegroundColor Cyan
    Write-Host '[System.Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", "your_secret", "User")' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Method 3 - Create .env file:" -ForegroundColor Yellow
    
    # Create sample .env file
    $envContent = @"
# AWS Credentials for ACEBotV2
# Replace with your actual AWS credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
"@
    
    $envContent | Out-File -FilePath ".env.example" -Encoding UTF8
    Write-Host "✓ Created .env.example file with template" -ForegroundColor Green
    Write-Host "Copy .env.example to .env and fill in your credentials" -ForegroundColor Cyan
} else {
    Write-Host "✓ AWS credentials found in environment variables" -ForegroundColor Green
}

# Create PowerShell profile helper (optional)
Write-Host "`n" + "=" * 40 -ForegroundColor Cyan
Write-Host "PowerShell Helper Functions" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

$helperFunctions = @"
# ACEBotV2 Helper Functions
# Add these to your PowerShell profile for convenience

function Start-ACEBot {
    param([int]`$Port = 8510)
    Push-Location "$PWD"
    python -m streamlit run app.py --server.port `$Port --server.address localhost
    Pop-Location
}

function Set-AWSCredentials {
    param(
        [Parameter(Mandatory=`$true)]
        [string]`$AccessKey,
        [Parameter(Mandatory=`$true)]
        [string]`$SecretKey,
        [string]`$Region = "us-east-1"
    )
    `$env:AWS_ACCESS_KEY_ID = `$AccessKey
    `$env:AWS_SECRET_ACCESS_KEY = `$SecretKey
    `$env:AWS_DEFAULT_REGION = `$Region
    Write-Host "✓ AWS credentials set for current session" -ForegroundColor Green
}
"@

$helperFunctions | Out-File -FilePath "acebot-helpers.ps1" -Encoding UTF8
Write-Host "✓ Created acebot-helpers.ps1 with convenience functions" -ForegroundColor Green

# Final instructions
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Set your AWS credentials (see methods above)" -ForegroundColor White
Write-Host "2. Run the app:" -ForegroundColor White
Write-Host "   .\run_local.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "The app will start at: http://localhost:8510" -ForegroundColor Yellow
Write-Host ""
Write-Host "Optional: Load helper functions with:" -ForegroundColor White
Write-Host ". .\acebot-helpers.ps1" -ForegroundColor Cyan
Write-Host "Then use: Start-ACEBot" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Green