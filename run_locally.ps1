# Run BigTB6 Locally on Windows

Write-Host "Starting BigTB6 Services..."
Write-Host "Opening new windows for Backend and Frontend..."

# Get absolute path to the project root
$ProjectRoot = Get-Location

# 1. Start Backend API
$BackendArgs = "-ExecutionPolicy Bypass -NoExit -Command cd '$ProjectRoot\server'; .\.venv\Scripts\python.exe main.py"
Start-Process powershell -ArgumentList $BackendArgs -WindowStyle Normal

# 2. Start Next.js Frontend
$FrontendArgs = "-ExecutionPolicy Bypass -NoExit -Command cd '$ProjectRoot\client'; npm run dev"
Start-Process powershell -ArgumentList $FrontendArgs -WindowStyle Normal

Write-Host "All services have been started in new windows!"
Write-Host "The Bot is now automatically spawned by the backend when you click Connect!"
Write-Host "You can access the frontend at: http://localhost:3000"
