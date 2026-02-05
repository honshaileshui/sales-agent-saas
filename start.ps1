# SalesAgent AI - Startup Script for Windows
# This script starts both backend and frontend simultaneously

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SalesAgent AI - Starting Services   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory (project root)
$projectRoot = $PSScriptRoot

# Start Backend in new window
Write-Host "[1/2] Starting Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; Write-Host 'Backend Server Starting...' -ForegroundColor Green; uvicorn api.main:app --reload --port 8000"

# Wait 3 seconds for backend to initialize
Write-Host "      Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Start Frontend in new window
Write-Host "[2/2] Starting Frontend (React + Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; Write-Host 'Frontend Server Starting...' -ForegroundColor Green; npm run dev"

# Wait for services to start
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Services Started Successfully! ✓   " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API:  " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:     " -NoNewline
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend:     " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop servers" -ForegroundColor Gray
Write-Host ""

# Keep this window open
Write-Host "This window will close in 5 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 5
