# run_docker.ps1 - Docker version of ACEBot
Write-Host "Starting ACEBot with Docker..." -ForegroundColor Green

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copy docker-env-example.txt to .env and configure your settings." -ForegroundColor Yellow
    Write-Host "Example: Copy-Item docker-env-example.txt .env" -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose is available
try {
    $null = Get-Command docker-compose -ErrorAction Stop
    Write-Host "Using docker-compose..." -ForegroundColor Blue
    docker-compose up --build
} catch {
    Write-Host "docker-compose not found, trying docker compose..." -ForegroundColor Blue
    try {
        $null = Get-Command docker -ErrorAction Stop
        docker compose up --build
    } catch {
        Write-Host "Error: Docker is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
}
