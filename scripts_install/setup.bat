@echo off
REM ============================================================================
REM Installation complete (Windows) -- Gestion de Cimetiere GI2 2026 v2
REM A executer UNE SEULE FOIS, depuis la racine du projet (cimetiere_gi2\).
REM
REM Usage : double-cliquez sur ce fichier, OU dans une invite de commandes :
REM   scripts_install\setup.bat
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0\.."
set PROJECT_ROOT=%CD%
set BACKEND_DIR=%PROJECT_ROOT%\backend
set FRONTEND_DIR=%PROJECT_ROOT%\frontend

echo ============================================================
echo  Installation -- Gestion de Cimetiere GI2 2026 v2 (Windows)
echo ============================================================

REM --- 1. Verification des prerequis -----------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python n'a pas ete trouve dans le PATH. Installez Python 3.11+ depuis
    echo     https://www.python.org/downloads/ en cochant "Add Python to PATH",
    echo     puis relancez ce script.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% detecte.

where psql >nul 2>nul
if errorlevel 1 (
    echo [ATTENTION] Le client 'psql' n'a pas ete trouve dans le PATH.
    echo     Assurez-vous qu'un serveur PostgreSQL est installe et accessible
    echo     avant de continuer ^(https://www.postgresql.org/download/windows/^).
) else (
    echo [OK] Client PostgreSQL detecte.
)

REM --- 2. Backend --------------------------------------------------------------
echo.
echo ------------------------------------------------------------
echo  BACKEND ^(Django + Django Ninja + PostgreSQL^)
echo ------------------------------------------------------------
cd /d "%BACKEND_DIR%"

if not exist "venv" (
    echo [->] Creation de l'environnement virtuel Python ^(backend\venv^)...
    python -m venv venv
    echo [OK] Environnement virtuel cree.
) else (
    echo [OK] Environnement virtuel deja present, reutilisation.
)

echo [->] Installation des dependances backend...
"%BACKEND_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip -q
"%BACKEND_DIR%\venv\Scripts\pip.exe" install -r requirements.txt -q
if errorlevel 1 (
    echo [X] Echec de l'installation des dependances backend.
    pause
    exit /b 1
)
echo [OK] Dependances backend installees.

set NEEDS_ENV_EDIT=0
if not exist ".env" (
    copy .env.example .env >nul
    echo [ATTENTION] Fichier backend\.env cree a partir de .env.example.
    echo     -^> OUVREZ backend\.env et renseignez au minimum :
    echo        DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    echo     -^> Optionnel mais recommande : GOOGLE_MAPS_API_KEY, MOMO_*
    set NEEDS_ENV_EDIT=1
) else (
    echo [OK] Fichier backend\.env deja present, non modifie.
)

if !NEEDS_ENV_EDIT!==1 (
    echo.
    set /p REPLY="Avez-vous fini d'editer backend\.env avec vos vraies valeurs ? [o/N] "
    if /i not "!REPLY!"=="o" (
        echo [ATTENTION] Installation interrompue. Editez backend\.env puis relancez ce script.
        pause
        exit /b 0
    )
)

echo [->] Application des migrations de base de donnees...
"%BACKEND_DIR%\venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 (
    echo [X] Echec des migrations. Verifiez la configuration PostgreSQL dans
    echo     backend\.env ^(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT^),
    echo     puis relancez ce script.
    pause
    exit /b 1
)
echo [OK] Migrations appliquees avec succes.

echo.
echo [->] Creation du premier compte administrateur.
set /p ADMIN_EMAIL="  Email de l'administrateur : "
set /p ADMIN_PASSWORD="  Mot de passe (8+ caracteres, visible a l'ecran) : "
set /p ADMIN_NAME="  Nom complet : "

"%BACKEND_DIR%\venv\Scripts\python.exe" manage.py bootstrap_admin --email "%ADMIN_EMAIL%" --password "%ADMIN_PASSWORD%" --full-name "%ADMIN_NAME%"
if errorlevel 1 (
    echo [ATTENTION] La creation de l'admin a echoue ^(existe peut-etre deja^). Vous pourrez reessayer plus tard avec :
    echo     backend\venv\Scripts\python.exe backend\manage.py bootstrap_admin --email ... --password ... --full-name ...
) else (
    echo [OK] Compte administrateur cree : %ADMIN_EMAIL%
)

echo [->] Collecte des fichiers statiques...
"%BACKEND_DIR%\venv\Scripts\python.exe" manage.py collectstatic --noinput
echo [OK] Backend pret.

REM --- 3. Frontend ---------------------------------------------------------------
echo.
echo ------------------------------------------------------------
echo  FRONTEND ^(Flet -- mode web^)
echo ------------------------------------------------------------
cd /d "%FRONTEND_DIR%"

if not exist "venv" (
    echo [->] Creation de l'environnement virtuel Python ^(frontend\venv^)...
    python -m venv venv
    echo [OK] Environnement virtuel cree.
) else (
    echo [OK] Environnement virtuel deja present, reutilisation.
)

echo [->] Installation des dependances frontend...
"%FRONTEND_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip -q
"%FRONTEND_DIR%\venv\Scripts\pip.exe" install -r requirements.txt -q
if errorlevel 1 (
    echo [X] Echec de l'installation des dependances frontend.
    pause
    exit /b 1
)
echo [OK] Dependances frontend installees.

if not exist ".env" (
    copy .env.example .env >nul
    echo [OK] Fichier frontend\.env cree ^(valeurs par defaut : API sur http://localhost:8000/api, port 8550^).
) else (
    echo [OK] Fichier frontend\.env deja present, non modifie.
)

echo.
echo ============================================================
echo [OK] INSTALLATION TERMINEE.
echo ============================================================
echo.
echo Pour lancer l'application, utilisez ^(dans deux invites de commandes separees^) :
echo.
echo   Fenetre 1 (backend)  : scripts_install\start_backend.bat
echo   Fenetre 2 (frontend) : scripts_install\start_frontend.bat
echo.
echo Puis ouvrez votre navigateur sur : http://localhost:8550
echo.
pause
