@echo off
setlocal enabledelayedexpansion

:: ─── Load public key from pem file ───────────────────────────
set "PEM_FILE=%~dp0..\jwt-keys\public.pem"

if not exist "%PEM_FILE%" (
    echo [ERROR] public.pem not found at %PEM_FILE%
    exit /b 1
)

:: Read the pem into a single env var preserving newlines
set "JWT_PUBLIC_KEY="
for /f "delims=" %%L in (%PEM_FILE%) do (
    if defined JWT_PUBLIC_KEY (
        set "JWT_PUBLIC_KEY=!JWT_PUBLIC_KEY!\n%%L"
    ) else (
        set "JWT_PUBLIC_KEY=%%L"
    )
)

echo [OK] JWT_PUBLIC_KEY loaded from public.pem
echo.

echo Starting infra (Kong + databases + redis and eventually all the services)...
cd /d "%~dp0..\infra"
docker compose up -d

echo Waiting for Kong to be ready...
timeout /t 8 /nobreak >nul

:: ─── Verify Kong loaded the key ───────────────────────────────
echo Verifying Kong consumer...
curl -s http://localhost:8010/consumers/onechan-app/jwt | findstr "1chan-server" >nul
if %errorlevel% == 0 (
    echo [OK] Kong consumer verified - 1chan-server key found
) else (
    echo [WARN] Kong consumer check failed - JWT_PUBLIC_KEY may not have loaded
    echo        Run: curl http://localhost:8010/consumers/onechan-app/jwt
)
echo.

:: ─── Start services ───────────────────────────────────────────
echo Starting services...
echo AuthService         -^> http://localhost:8001
echo NotificationService -^> http://localhost:8002
echo PostService         -^> http://localhost:8003
echo FeedService         -^> http://localhost:8004
echo Kong Proxy          -^> http://localhost:8000
echo Kong Admin          -^> http://localhost:8010
echo.

start "AuthService"         cmd /k cd /d "%~dp0..\services\AuthService"         ^&^& uv run python -m uvicorn src.main:app --port 8001 --reload
start "NotificationService" cmd /k cd /d "%~dp0..\services\NotificationService" ^&^& uv run python -m uvicorn src.main:app --port 8002 --reload
start "PostService"         cmd /k cd /d "%~dp0..\services\PostService"         ^&^& uv run python -m uvicorn src.main:app --port 8003 --reload
start "FeedService"         cmd /k cd /d "%~dp0..\services\FeedService"         ^&^& uv run python -m uvicorn src.main:app --port 8004 --reload

echo All services launched.
echo.
echo Quick test:
echo   curl http://localhost:8000/api/v1/posts        [expect 401]
echo   curl http://localhost:8000/api/v1/free_auth    [expect 200]

endlocal