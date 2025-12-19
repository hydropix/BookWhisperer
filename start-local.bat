@echo off
REM ============================================
REM BookWhisperer - Local Development Launcher
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo    BookWhisperer - Local Development
echo ============================================
echo.
echo [DEBUG] Script started successfully
echo [DEBUG] Current directory: %CD%
echo.
timeout /t 2 /nobreak >nul

REM Configuration
set PYTHON_CMD=python
set NODE_CMD=npm
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend

REM Check if this is first run or update
set FIRST_RUN=0
if not exist "%BACKEND_DIR%\.env" set FIRST_RUN=1
if not exist "%BACKEND_DIR%\venv" set FIRST_RUN=1
if not exist "%FRONTEND_DIR%\node_modules" set FIRST_RUN=1

if %FIRST_RUN%==1 (
    echo [INFO] First run detected - will install dependencies
) else (
    echo [INFO] Existing installation detected - will update if needed
)

echo.
echo ============================================
echo  Step 1/6: Checking Prerequisites
echo ============================================
echo.

REM Check Python
echo [DEBUG] Checking for Python...
%PYTHON_CMD% --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Python found
%PYTHON_CMD% --version

REM Check Node.js
echo.
echo [DEBUG] Checking for Node.js...
call %NODE_CMD% --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    echo Download from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js found
call %NODE_CMD% --version

REM Check Docker (for database services)
echo.
echo [DEBUG] Checking for Docker...
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Docker not found! You'll need PostgreSQL and Redis running separately.
    echo Download Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo.
    set DOCKER_AVAILABLE=0
) else (
    echo [OK] Docker found
    docker --version
    set DOCKER_AVAILABLE=1
)

echo.
echo ============================================
echo  Step 2/6: Backend Configuration
echo ============================================
echo.

echo [DEBUG] Changing to backend directory...
if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    echo [ERROR] Current directory: %CD%
    echo [ERROR] Please run this script from the BookWhisperer root directory
    echo.
    pause
    exit /b 1
)

cd %BACKEND_DIR%
echo [DEBUG] Now in: %CD%

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating backend .env file...

    if not exist ".env.example" (
        echo [ERROR] .env.example not found in backend directory
        cd ..
        pause
        exit /b 1
    )

    copy .env.example .env >nul
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create .env file
        cd ..
        pause
        exit /b 1
    )

    echo.
    echo [IMPORTANT] Please configure your backend/.env file:
    echo.
    echo   - DATABASE_URL: PostgreSQL connection string
    echo   - REDIS_URL: Redis connection string
    echo   - OLLAMA_URL: Remote Ollama API URL (e.g., http://your-server:11434)
    echo   - OLLAMA_MODEL: Model name (default: llama2)
    echo.

    REM Prompt for Ollama URL
    echo [CONFIG] Ollama Configuration
    set /p OLLAMA_URL="Enter Ollama API URL (default: http://localhost:11434): "
    if "!OLLAMA_URL!"=="" set OLLAMA_URL=http://localhost:11434

    set /p OLLAMA_MODEL="Enter Ollama model name (default: llama2): "
    if "!OLLAMA_MODEL!"=="" set OLLAMA_MODEL=llama2

    echo [DEBUG] Updating .env with Ollama settings...
    REM Update .env file with Ollama settings
    powershell -Command "(Get-Content .env) -replace 'OLLAMA_URL=.*', 'OLLAMA_URL=!OLLAMA_URL!' | Set-Content .env" 2>nul
    powershell -Command "(Get-Content .env) -replace 'OLLAMA_MODEL=.*', 'OLLAMA_MODEL=!OLLAMA_MODEL!' | Set-Content .env" 2>nul

    echo [OK] .env file created and configured
) else (
    echo [OK] Backend .env file already exists
)

echo.
echo ============================================
echo  Step 3/6: Backend Dependencies
echo ============================================
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment and install/update dependencies
echo [INFO] Installing/updating Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    cd ..
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

REM Create storage directories
if not exist "storage\uploads" mkdir "storage\uploads"
if not exist "storage\audio" mkdir "storage\audio"
echo [OK] Storage directories ready

cd ..

echo.
echo ============================================
echo  Step 4/6: Frontend Configuration
echo ============================================
echo.

cd %FRONTEND_DIR%

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating frontend .env file...
    copy .env.example .env >nul
    echo [OK] Frontend .env file created
) else (
    echo [OK] Frontend .env file already exists
)

echo.
echo ============================================
echo  Step 5/6: Frontend Dependencies
echo ============================================
echo.

REM Install/update Node.js dependencies
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies (this may take a few minutes)...
    call %NODE_CMD% install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Node.js dependencies installed
) else (
    echo [INFO] Updating Node.js dependencies...
    call %NODE_CMD% install
    echo [OK] Node.js dependencies updated
)

cd ..

echo.
echo ============================================
echo  Step 6/6: Starting Services
echo ============================================
echo.

REM Start Docker services if Docker is available
if %DOCKER_AVAILABLE%==1 (
    echo [INFO] Starting Docker services (PostgreSQL, Redis)...
    docker-compose up -d db redis
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to start Docker services
        echo [INFO] Please ensure PostgreSQL and Redis are running manually
    ) else (
        echo [OK] Docker services started
        echo [INFO] Waiting 5 seconds for services to initialize...
        timeout /t 5 /nobreak >nul
    )
) else (
    echo [WARNING] Docker not available - ensure PostgreSQL and Redis are running manually
)

REM Run database migrations
echo.
echo [INFO] Running database migrations...
cd %BACKEND_DIR%
call venv\Scripts\activate.bat
alembic upgrade head
if %errorlevel% neq 0 (
    echo [WARNING] Database migrations failed - you may need to configure DATABASE_URL in backend/.env
)
cd ..

echo.
echo ============================================
echo  Launching Application
echo ============================================
echo.

echo [INFO] Starting backend and frontend servers...
echo.
echo The following services will be started:
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Frontend: http://localhost:3000
echo   - Celery Worker (async tasks)
echo.

REM Create launcher script for backend
echo @echo off > start-backend.bat
echo cd backend >> start-backend.bat
echo call venv\Scripts\activate.bat >> start-backend.bat
echo echo [BACKEND] Starting FastAPI server... >> start-backend.bat
echo uvicorn app.main:app --reload >> start-backend.bat

REM Create launcher script for Celery worker
echo @echo off > start-celery.bat
echo cd backend >> start-celery.bat
echo call venv\Scripts\activate.bat >> start-celery.bat
echo echo [CELERY] Starting Celery worker... >> start-celery.bat
echo celery -A app.tasks.celery_app worker --loglevel=info --pool=solo >> start-celery.bat

REM Create launcher script for frontend
echo @echo off > start-frontend.bat
echo cd frontend >> start-frontend.bat
echo echo [FRONTEND] Starting Vite dev server... >> start-frontend.bat
echo npm run dev >> start-frontend.bat

echo [INFO] Launching services in separate windows...
echo.

REM Start services in new windows
start "BookWhisperer - Backend API" cmd /k start-backend.bat
timeout /t 2 /nobreak >nul
start "BookWhisperer - Celery Worker" cmd /k start-celery.bat
timeout /t 2 /nobreak >nul
start "BookWhisperer - Frontend" cmd /k start-frontend.bat

echo.
echo ============================================
echo  BookWhisperer is Starting!
echo ============================================
echo.
echo Three windows have been opened:
echo   1. Backend API Server (http://localhost:8000)
echo   2. Celery Worker (async processing)
echo   3. Frontend Dev Server (http://localhost:3000)
echo.
echo Wait a few seconds for all services to start, then open:
echo   http://localhost:3000
echo.
echo To stop all services:
echo   - Close all three command windows
echo   - Or press Ctrl+C in each window
echo.
if %DOCKER_AVAILABLE%==1 (
    echo To stop Docker services:
    echo   docker-compose down
    echo.
)
echo ============================================
echo.

echo.
echo ============================================
echo  Script completed!
echo ============================================
echo.
echo Press any key to exit...
pause
endlocal
exit /b 0
