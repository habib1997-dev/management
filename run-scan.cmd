@echo off
setlocal
REM ============================================================
REM  One-click SonarQube scan helper for the management project.
REM
REM  Usage:  run-scan.cmd [frontend|backend]
REM          (defaults to "backend" when no argument is given)
REM
REM  Reads sonar-project.properties from the chosen project dir,
REM  runs the scanner, then opens that project's dashboard.
REM ============================================================

set "SONAR_URL=http://localhost:9000"
set "SONAR_TOKEN=REMOVED"
set "SCANNER=C:\sonar-scanner\bin\sonar-scanner.bat"

set "PROJECT=%~1"
if "%PROJECT%"=="" set "PROJECT=backend"

if /i "%PROJECT%"=="frontend" (
    set "PROJECT_DIR=C:\Users\Naqeeb\Desktop\management\frontend"
    set "PROJECT_KEY=management-frontend"
) else if /i "%PROJECT%"=="backend" (
    set "PROJECT_DIR=C:\Users\Naqeeb\Desktop\management\backend"
    set "PROJECT_KEY=management-backend"
) else (
    echo Unknown project "%PROJECT%". Use: run-scan.cmd frontend ^| run-scan.cmd backend
    exit /b 1
)

if not exist "%PROJECT_DIR%\sonar-project.properties" (
    echo Missing "%PROJECT_DIR%\sonar-project.properties"
    exit /b 1
)

echo ============================================================
echo  Scanning project: %PROJECT%   (key=%PROJECT_KEY%)
echo ============================================================

pushd "%PROJECT_DIR%"
"%SCANNER%" -Dsonar.host.url=%SONAR_URL% -Dsonar.token=%SONAR_TOKEN%
set "RC=%ERRORLEVEL%"
popd

if not "%RC%"=="0" (
    echo.
    echo Scan failed ^(exit code %RC%^).
    exit /b %RC%
)

echo.
echo Scan complete - opening dashboard...
start "" "%SONAR_URL%/dashboard?id=%PROJECT_KEY%"
endlocal
exit /b 0