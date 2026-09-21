# Rocket League Replay Analyzer — Multi-Service Launcher
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Rocket League AI Replay Analyzer System        " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot

# 1. Start Python ML FastAPI Microservice (Port 8000)
Write-Host "[1/3] Starting Python ML Engine on port 8000..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\ml-service'; .venv\Scripts\uvicorn api.main_api:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start C# .NET Gateway API (Port 5000)
Write-Host "[2/3] Starting C# .NET Gateway API on port 5000..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\gateway-api'; dotnet run --urls 'http://127.0.0.1:5000'"

# 3. Start React Frontend Dashboard (Port 5173)
Write-Host "[3/3] Starting React Dashboard on port 5173..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\rl-analyzer-ui'; npm run dev"

Write-Host "All services launched successfully!" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host "API Gateway Swagger: http://localhost:5000/swagger" -ForegroundColor White
Write-Host "Python ML API: http://127.0.0.1:8000/docs" -ForegroundColor White
