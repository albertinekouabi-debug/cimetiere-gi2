@echo off
REM ============================================================================
REM Lance la suite de tests de regression (backend + frontend) contre un
REM backend de developpement demarre temporairement pour l'occasion (Windows).
REM
REM Usage : scripts_install\run_tests.bat
REM ============================================================================
cd /d "%~dp0\.."
set PROJECT_ROOT=%CD%
set BACKEND_DIR=%PROJECT_ROOT%\backend
set FRONTEND_DIR=%PROJECT_ROOT%\frontend

if not exist "%BACKEND_DIR%\venv" (
    echo [X] Installation incomplete. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)
if not exist "%FRONTEND_DIR%\venv" (
    echo [X] Installation incomplete. Executez d'abord : scripts_install\setup.bat
    pause
    exit /b 1
)

echo [->] Demarrage temporaire du backend pour les tests...
cd /d "%BACKEND_DIR%"

REM Demarre le serveur en arriere-plan via PowerShell et conserve son PID
powershell -NoProfile -Command ^
  "$p = Start-Process -FilePath '%BACKEND_DIR%\venv\Scripts\python.exe' -ArgumentList 'manage.py runserver 127.0.0.1:8123 --noreload' -WorkingDirectory '%BACKEND_DIR%' -RedirectStandardOutput '%TEMP%\cimetiere_test_server.log' -RedirectStandardError '%TEMP%\cimetiere_test_server_err.log' -PassThru -WindowStyle Hidden; $p.Id | Out-File -FilePath '%TEMP%\cimetiere_test_server.pid' -Encoding ascii"

timeout /t 3 /nobreak >nul

echo.
echo === Regression API backend ===
"%BACKEND_DIR%\venv\Scripts\python.exe" scripts\regression_test.py
set BACKEND_RESULT=%ERRORLEVEL%

echo.
echo === Tests des pages frontend ===
cd /d "%FRONTEND_DIR%"
set API_BASE_URL=http://127.0.0.1:8123/api
"%FRONTEND_DIR%\venv\Scripts\python.exe" scripts\test_pages.py
set FRONTEND_RESULT=%ERRORLEVEL%

echo.
echo [->] Arret du serveur de test...
for /f %%i in (%TEMP%\cimetiere_test_server.pid) do taskkill /PID %%i /F >nul 2>nul

if %BACKEND_RESULT% neq 0 (
    echo [X] Des tests backend ont echoue. Voir %TEMP%\cimetiere_test_server_err.log pour les logs serveur.
    pause
    exit /b 1
)
if %FRONTEND_RESULT% neq 0 (
    echo [X] Des tests frontend ont echoue.
    pause
    exit /b 1
)

echo.
echo [OK] TOUS LES TESTS SONT PASSES.
pause
