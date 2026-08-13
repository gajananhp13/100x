@echo off
setlocal
cd /d "%~dp0"

echo.
echo  ============================================
echo  100x Resume - Candidate Verification Platform
echo  ============================================
echo.

if not exist "backend\.venv" (
    echo [setup] Creating Python virtual environment...
    python -m venv "backend\.venv"
    if errorlevel 1 goto :fail_python
)

echo [setup] Checking backend dependencies...
set NEED_BACKEND=0
"backend\.venv\Scripts\python.exe" -c "import fastapi, pydantic, fitz" >nul 2>&1 || set NEED_BACKEND=1
if "%NEED_BACKEND%"=="1" (
    echo [setup] Installing backend dependencies - first run, may take a while...
    "backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
    if errorlevel 1 goto :fail_pip
)

if not exist "frontend\node_modules" (
    echo [setup] Installing frontend dependencies - first run, may take a while...
    pushd "frontend"
    call npm install
    if errorlevel 1 (
        popd
        goto :fail_npm
    )
    popd
)

echo.
echo [start] Launching backend - report API on http://localhost:8000
REM Note: no --reload here -- on Windows the reloader can orphan a wedged
REM worker holding port 8000 (server becomes unresponsive, uploads fail with
REM ECONNRESET). Add --reload manually only for active backend development.
start "100x Resume - Backend" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

timeout /t 2 /nobreak >nul

echo [start] Launching frontend - UI on http://localhost:3000
start "100x Resume - Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

timeout /t 4 /nobreak >nul
echo.
echo  ============================================
echo  100x Resume is starting...
echo.
echo    UI       : http://localhost:3000
echo    API docs : http://localhost:8000/docs
echo.
echo  Tip: click "Load demo candidate" on the Connect step
echo       for a full end-to-end demo without any accounts.
echo  ============================================
echo.
endlocal
goto :eof

:fail_python
echo [error] Python 3.10+ not found. Install from https://www.python.org/downloads/
exit /b 1

:fail_pip
echo [error] Backend dependency install failed. See message above.
exit /b 1

:fail_npm
echo [error] Frontend dependency install failed. See message above.
exit /b 1