@echo off
REM ============================================================
REM SalesAgent AI - Professional Startup Script
REM ============================================================
REM This script starts both backend (FastAPI) and frontend (React/Vite)
REM Version: 2.0 - Production Ready
REM Author: Shailesh Hon
REM ============================================================

color 0A
title SalesAgent AI - Startup

echo.
echo ========================================================
echo.
echo     ███████╗ █████╗ ██╗     ███████╗███████╗
echo     ██╔════╝██╔══██╗██║     ██╔════╝██╔════╝
echo     ███████╗███████║██║     █████╗  ███████╗
echo     ╚════██║██╔══██║██║     ██╔══╝  ╚════██║
echo     ███████║██║  ██║███████╗███████╗███████║
echo     ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
echo.
echo           AI-Powered Sales Outreach Platform
echo.
echo ========================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [INFO] Activating Python virtual environment...
    if exist .venv\Scripts\activate.bat (
        call .venv\Scripts\activate.bat
        echo [SUCCESS] Virtual environment activated
    ) else (
        echo [WARNING] Virtual environment not found at .venv
        echo [INFO] Continuing without virtual environment...
    )
    echo.
)

echo [1/3] Starting Backend Server (FastAPI on port 8000)...
echo --------------------------------------------------------
start "SalesAgent Backend - FastAPI" cmd /k "cd /d %~dp0 && title Backend - FastAPI && color 0B && uvicorn api.main:app --reload --port 8000"
echo [SUCCESS] Backend starting in new window
echo.

REM Wait for backend to initialize
echo [INFO] Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak > nul

echo [2/3] Starting Frontend Server (React/Vite on port 5173)...
echo --------------------------------------------------------
start "SalesAgent Frontend - React" cmd /k "cd /d %~dp0\frontend && title Frontend - React/Vite && color 0E && npm run dev"
echo [SUCCESS] Frontend starting in new window
echo.

REM Wait for frontend to initialize
timeout /t 2 /nobreak > nul

echo [3/3] Opening Application in Browser...
echo --------------------------------------------------------
timeout /t 3 /nobreak > nul
start http://localhost:5173
echo [SUCCESS] Browser opened
echo.

echo ========================================================
echo.
echo     🚀 SalesAgent AI is now running!
echo.
echo     📊 Backend API:  http://localhost:8000
echo     📖 API Docs:     http://localhost:8000/docs
echo     🌐 Frontend:     http://localhost:5173
echo.
echo ========================================================
echo.
echo [INFO] Two terminal windows have been opened:
echo        1. Backend (Blue) - FastAPI server
echo        2. Frontend (Yellow) - React development server
echo.
echo [INFO] To stop the servers:
echo        - Close both terminal windows, OR
echo        - Press Ctrl+C in each window
echo.
echo [INFO] This window will close in 5 seconds...
echo ========================================================
echo.

timeout /t 5 /nobreak > nul
exit
