@echo off
REM Setup script for Ollama - pulls the required model

setlocal enabledelayedexpansion

if "%OLLAMA_URL%"=="" set OLLAMA_URL=http://localhost:11434
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=llama2

echo ============================================
echo Ollama Setup Script
echo ============================================
echo Ollama URL: %OLLAMA_URL%
echo Model to pull: %OLLAMA_MODEL%
echo.

REM Wait for Ollama to be ready
echo Waiting for Ollama service to be ready...
set max_attempts=30
set attempt=0

:wait_loop
if !attempt! geq !max_attempts! (
    echo ERROR: Ollama service did not become ready in time
    exit /b 1
)

curl -s "%OLLAMA_URL%/api/tags" >nul 2>&1
if %errorlevel% equ 0 (
    echo Ollama is ready!
    goto :check_model
)

set /a attempt+=1
echo Attempt !attempt!/!max_attempts! - Ollama not ready yet, waiting...
timeout /t 2 /nobreak >nul
goto :wait_loop

:check_model
echo.
echo Checking if model '%OLLAMA_MODEL%' is already available...

curl -s "%OLLAMA_URL%/api/tags" | findstr /C:"\"name\":\"%OLLAMA_MODEL%\"" >nul 2>&1
if %errorlevel% equ 0 (
    echo Model '%OLLAMA_MODEL%' is already available!
    echo Setup complete!
    exit /b 0
)

REM Pull the model
echo.
echo Model '%OLLAMA_MODEL%' not found. Pulling model...
echo This may take several minutes depending on model size...
echo.

curl -X POST "%OLLAMA_URL%/api/pull" ^
    -H "Content-Type: application/json" ^
    -d "{\"name\": \"%OLLAMA_MODEL%\"}"

if %errorlevel% neq 0 (
    echo ERROR: Failed to pull model '%OLLAMA_MODEL%'
    exit /b 1
)

echo.
echo ============================================
echo Setup complete! Model '%OLLAMA_MODEL%' is ready.
echo ============================================

endlocal
