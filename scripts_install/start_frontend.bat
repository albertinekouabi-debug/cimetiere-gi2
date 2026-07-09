@echo off
REM ============================================================================
REM Lance le frontend Flet (mode web) en developpement (Windows).
REM Prerequis :
REM   - avoir execute scripts_install\setup.bat au moins une fois
REM   - le backend doit deja etre demarre (scripts_install\start_backend.bat)
REM
REM Usage : scripts_install\start_frontend.bat
REM ============================================================================
cd /d "%~dp0\.."
set FRONTEND_DIR=%CD%\frontend

if not exist "%FRONTEND_DIR%\venv" (
    echo [X] Environnement virtuel introuvable. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\.env" (
    echo [X] frontend\.env introuvable. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)

cd /d "%FRONTEND_DIR%"
echo [->] Demarrage du frontend sur http://localhost:8550
echo     Assurez-vous que le backend tourne deja (scripts_install\start_backend.bat)
echo     Arret : Ctrl+C
echo.
"%FRONTEND_DIR%\venv\Scripts\python.exe" main.py
pause
