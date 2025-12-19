@echo off
REM ============================================
REM BookWhisperer - Stop
REM ============================================

echo.
echo ========================================
echo    Arret de BookWhisperer
echo ========================================
echo.

REM Fermer les fenetres des serveurs
taskkill /FI "WINDOWTITLE eq BookWhisperer-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BookWhisperer-Frontend*" /F >nul 2>&1

REM Arreter les containers Docker
echo Arret des services Docker...
docker-compose stop db redis >nul 2>&1

echo.
echo [OK] BookWhisperer arrete.
echo.
timeout /t 2 /nobreak >nul
