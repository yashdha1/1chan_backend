@echo off
setlocal

pushd "%~dp0.."
set "ROOT_DIR=%CD%\"
popd

echo Starting dev services...
echo AuthService         -^> http://localhost:8001
echo NotificationService -^> http://localhost:8002
echo PostService         -^> http://localhost:8003
echo FeedService         -^> http://localhost:8004
echo.

start "AuthService" cmd /k cd /d "%ROOT_DIR%services\AuthService" ^&^& uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
@REM start "NotificationService" cmd /k cd /d "%ROOT_DIR%services\NotificationService" ^&^& uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
start "PostService" cmd /k cd /d "%ROOT_DIR%services\PostService" ^&^& uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
@REM start "FeedService" cmd /k cd /d "%ROOT_DIR%services\FeedService" ^&^& uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload

echo Services launched in separate terminals.
echo If any service exits immediately, verify that service has a FastAPI app at src.main:app.

endlocal
