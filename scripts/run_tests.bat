@echo off
setlocal

set ROOT=%~dp0..\services
set FAILED=0

echo ============================================
echo  Running all service tests
echo ============================================

for %%S in (AuthService PostService FeedService NotificationService) do (
    echo.
    echo ------ %%S ------
    pushd "%ROOT%\%%S"
    call .venv\Scripts\python.exe -m pytest tests\ -v --tb=short
    if errorlevel 1 set FAILED=1
    popd
)

echo.
echo ============================================
if %FAILED%==1 (
    echo  SOME TESTS FAILED
    exit /b 1
) else (
    echo  ALL TESTS PASSED
    exit /b 0
)
