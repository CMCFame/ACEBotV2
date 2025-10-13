# run_simple_clean.ps1
Write-Host "Starting Simple ACE App..." -ForegroundColor Green

# Install dependencies
python -m pip install streamlit boto3 google-api-python-client google-auth

# Start the app
Write-Host "Opening app at http://localhost:8520" -ForegroundColor Yellow
python -m streamlit run simple_ace_app.py --server.port 8520