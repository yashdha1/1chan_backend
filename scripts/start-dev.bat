@echo off
setlocal

echo Starting dev services...
echo AuthService         -^> http://localhost:8001
echo NotificationService -^> http://localhost:8002
echo PostService         -^> http://localhost:8003
echo FeedService         -^> http://localhost:8004
echo.

@REM Paths are anchored to this script folder so cd works no matter where you run the bat from.
start "AuthService" cmd /k cd /d "%~dp0..\services\AuthService" ^&^& uv run python -m uvicorn src.main:app --port 8001 --reload
start "NotificationService" cmd /k cd /d "%~dp0..\services\NotificationService" ^&^& uv run python -m uvicorn src.main:app --port 8002 --reload
start "PostService" cmd /k cd /d "%~dp0..\services\PostService" ^&^& uv run python -m uvicorn src.main:app --port 8003 --reload
@REM start "FeedService" cmd /k cd /d "%~dp0..\services\FeedService" ^&^& uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload

echo Services launched in separate terminals.

endlocal
