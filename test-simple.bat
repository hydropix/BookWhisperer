@echo off
echo ============================================
echo Test Simple - BookWhisperer
echo ============================================
echo.
echo Etape 1: Affichage du repertoire actuel
echo Repertoire: %CD%
echo.
pause

echo.
echo Etape 2: Test Python
python --version
if %errorlevel% neq 0 (
    echo ERREUR: Python non trouve
) else (
    echo OK: Python trouve
)
echo.
pause

echo.
echo Etape 3: Test Node.js
npm --version
if %errorlevel% neq 0 (
    echo ERREUR: Node.js non trouve
) else (
    echo OK: Node.js trouve
)
echo.
pause

echo.
echo Etape 4: Test Docker
docker --version
if %errorlevel% neq 0 (
    echo ATTENTION: Docker non trouve
) else (
    echo OK: Docker trouve
)
echo.
pause

echo.
echo Etape 5: Verification repertoire backend
if exist "backend" (
    echo OK: Dossier backend trouve
    cd backend
    echo Maintenant dans: %CD%
    if exist ".env.example" (
        echo OK: .env.example trouve
    ) else (
        echo ERREUR: .env.example non trouve
    )
    cd ..
) else (
    echo ERREUR: Dossier backend non trouve
)
echo.
pause

echo.
echo Etape 6: Verification repertoire frontend
if exist "frontend" (
    echo OK: Dossier frontend trouve
    cd frontend
    echo Maintenant dans: %CD%
    if exist "package.json" (
        echo OK: package.json trouve
    ) else (
        echo ERREUR: package.json non trouve
    )
    cd ..
) else (
    echo ERREUR: Dossier frontend non trouve
)
echo.
pause

echo.
echo ============================================
echo Test termine!
echo ============================================
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
