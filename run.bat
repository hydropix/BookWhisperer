@echo off
REM ============================================
REM BookWhisperer - Quick Start (Double-clic!)
REM ============================================

echo.
echo ========================================
echo    BookWhisperer - Demarrage rapide
echo ========================================
echo.

REM Verifier si c'est la premiere fois
if not exist "backend\venv" goto :install
if not exist "frontend\node_modules" goto :install
goto :start

:install
echo [1/4] Premiere utilisation - Installation...
echo.

REM Installation backend
echo       - Backend Python...
cd backend
if not exist ".env" copy .env.example .env >nul 2>&1
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Echec de l'installation des dependances Python!
    echo.
    cd ..
    pause
    exit /b 1
)
if not exist "storage\uploads" mkdir "storage\uploads"
if not exist "storage\audio" mkdir "storage\audio"

REM Initialisation de la base de donnees SQLite
echo       - Initialisation base de donnees SQLite...
python init_db.py
cd ..

REM Installation frontend
echo       - Frontend Node.js...
cd frontend
if not exist ".env" copy .env.example .env >nul 2>&1
call npm install
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Echec de l'installation des dependances Node.js!
    echo.
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [OK] Installation terminee!
echo.
goto :startservers

:start
echo [1/4] Verification base de donnees...
cd backend
call venv\Scripts\activate.bat
if not exist "bookwhisperer.db" python init_db.py
cd ..

:startservers
REM Nettoyer les anciens processus au cas ou
call :cleanup_silent

echo [2/4] Demarrage du backend (port 8000)...
cd backend
start "BookWhisperer-Backend" /min cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --reload"
cd ..

echo [3/4] Demarrage du frontend (port 3000)...
cd frontend
start "BookWhisperer-Frontend" /min cmd /c "npm run dev"
cd ..

echo.
echo En attente du demarrage (5 secondes)...
timeout /t 5 /nobreak >nul

REM Ouvrir le navigateur
echo [4/4] Ouverture du navigateur...
start http://localhost:3000

echo.
echo ========================================
echo    BookWhisperer est pret!
echo ========================================
echo.
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo ----------------------------------------
echo  FERMER: Appuyez sur une touche ici
echo          ou fermez simplement cette
echo          fenetre (tout s'arretera)
echo ----------------------------------------
echo.
pause >nul
goto :cleanup

:cleanup_silent
taskkill /fi "WINDOWTITLE eq BookWhisperer-Backend*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq BookWhisperer-Frontend*" /f >nul 2>&1
exit /b

:cleanup
echo.
echo Arret des serveurs...
taskkill /fi "WINDOWTITLE eq BookWhisperer-Backend*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq BookWhisperer-Frontend*" /f >nul 2>&1
echo [OK] BookWhisperer arrete.
