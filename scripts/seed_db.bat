@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

echo Seeding all databases...
echo.

echo [1/4] AuthDB
pushd "%SCRIPT_DIR%..\services\AuthService"
uv run --with faker python "seed_auth_db.py"
if errorlevel 1 (
  popd
  echo AuthDB seeding failed.
  exit /b 1
)
popd

echo [2/4] PostDB
pushd "%SCRIPT_DIR%..\services\PostService"
uv run --with faker python "seed_post_db.py"
if errorlevel 1 (
  popd
  echo PostDB seeding failed.
  exit /b 1
)
popd

echo [3/4] FeedDB
pushd "%SCRIPT_DIR%..\services\FeedService"
uv run --with faker python "seed_feed_db.py"
if errorlevel 1 (
  popd
  echo FeedDB seeding failed.
  exit /b 1
)
popd

echo [4/4] NotificationDB
pushd "%SCRIPT_DIR%..\services\NotificationService"
uv run --with faker python "seed_notification_db.py"
if errorlevel 1 (
  popd
  echo NotificationDB seeding failed.
  exit /b 1
)
popd

echo.
echo All database seeders completed.
endlocal
