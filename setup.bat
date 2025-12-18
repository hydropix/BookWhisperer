@echo off
echo === BookWhisperer Setup ===
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose are installed
echo.

REM Create .env file if it doesn't exist
if not exist backend\.env (
    echo Creating .env file from .env.example...
    copy backend\.env.example backend\.env >nul
    echo [OK] Created backend\.env
    echo [WARNING] Please edit backend\.env to configure your settings
) else (
    echo [OK] backend\.env already exists
)

echo.

REM Create storage directories
echo Creating storage directories...
if not exist backend\storage\uploads mkdir backend\storage\uploads
if not exist backend\storage\audio mkdir backend\storage\audio
type nul > backend\storage\uploads\.gitkeep
type nul > backend\storage\audio\.gitkeep
echo [OK] Storage directories created
echo.

REM Start Docker containers
echo Starting Docker containers...
docker-compose up -d db redis ollama
echo [OK] Database, Redis, and Ollama containers started
echo.

REM Wait for database to be ready
echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Build and start backend
echo Building backend container...
docker-compose build backend
echo [OK] Backend container built
echo.

echo Starting backend services...
docker-compose up -d backend celery_worker flower
echo [OK] Backend services started
echo.

echo === Setup Complete ===
echo.
echo Services available at:
echo   - API Documentation: http://localhost:8000/docs
echo   - API: http://localhost:8000
echo   - Flower (Celery monitoring): http://localhost:5555
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
echo   - Ollama: http://localhost:11434
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down
echo.
echo Note: You may need to pull an Ollama model:
echo   docker exec -it bookwhisperer_ollama ollama pull llama2
echo.
pause
