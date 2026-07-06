@echo off
cd /d "%~dp0"
start "Stock Tracker Backend" cmd /k "cd backend && ..\.venv\Scripts\python -m uvicorn main:app --port 8000"
start "Stock Tracker Frontend" cmd /k "cd frontend && npm run dev"
