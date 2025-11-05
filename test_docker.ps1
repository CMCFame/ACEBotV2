# test_docker.ps1 - Test Docker setup
Write-Host "Testing Docker setup for ACEBotV2..." -ForegroundColor Green

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>$null
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
try {
    $composeVersion = docker-compose --version 2>$null
    Write-Host "✓ Docker Compose available: $composeVersion" -ForegroundColor Green
} catch {
    try {
        $composeVersion = docker compose version 2>$null
        Write-Host "✓ Docker Compose (v2) available: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker Compose not found." -ForegroundColor Red
        exit 1
    }
}

# Check if required files exist
$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "simple_ace_app.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file found" -ForegroundColor Green
    } else {
        Write-Host "✗ $file missing" -ForegroundColor Red
        exit 1
    }
}

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "! .env file not found. Copy docker-env-example.txt to .env and configure." -ForegroundColor Yellow
    Write-Host "  Example: Copy-Item docker-env-example.txt .env" -ForegroundColor Yellow
}

Write-Host "`n🎉 Docker setup looks good!" -ForegroundColor Green
Write-Host "Run '.\run_docker.ps1' to start the application." -ForegroundColor Cyan
