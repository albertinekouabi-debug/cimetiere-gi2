@echo off
REM ============================================================================
REM Lance le backend Django (API) en mode developpement (Windows).
REM Prerequis : avoir execute scripts_install\setup.bat au moins une fois.
REM
REM Usage : scripts_install\start_backend.bat
REM ============================================================================
cd /d "%~dp0\.."
set BACKEND_DIR=%CD%\backend

if not exist "%BACKEND_DIR%\venv" (
    echo [X] Environnement virtuel introuvable. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%\.env" (
    echo [X] backend\.env introuvable. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"
echo [->] Demarrage du backend sur http://localhost:8000 (API sur /api, admin Django sur /admin)
echo     Arret : Ctrl+C
echo.
"%BACKEND_DIR%\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
pause
