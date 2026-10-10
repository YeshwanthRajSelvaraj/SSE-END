@echo off
title EcoSmart Platform Server Launcher
color 0A
echo =====================================================================
echo        EcoSmart Zero-Trust Waste Management Platform Launcher
echo =====================================================================
echo.
echo [1/2] Starting FastAPI Backend on port 8001...
start "EcoSmart Backend (Port 8001)" cmd /k "cd /d \"%~dp0backend\" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend Command Center on port 3000...
start "EcoSmart Frontend (Port 3000)" cmd /k "cd /d \"%~dp0frontend\" && python -m http.server 3000 --bind 127.0.0.1"

timeout /t 2 /nobreak >nul

echo.
echo =====================================================================
echo   [SUCCESS] Both servers are running!
echo   - Frontend Command Center: http://127.0.0.1:3000
echo   - Direct Frontend (via API): http://127.0.0.1:8001/
echo   - Interactive Swagger Docs: http://127.0.0.1:8001/docs
echo   - Health Check Probe:       http://127.0.0.1:8001/api/health
echo =====================================================================
echo.
echo Press any key to exit this launcher window (servers will remain running).
pause >nul
