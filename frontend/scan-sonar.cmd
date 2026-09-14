@echo off
REM Scans the React frontend against the local SonarQube server (localhost:9000).
REM Requires the server to be running and SONAR_TOKEN set.
if "%SONAR_TOKEN%"=="" (
  echo ERROR: SONAR_TOKEN is not set. Generate one in SonarQube UI ^> My Account ^> Security.
  exit /b 1
)
cd /d "%~dp0"
sonar-scanner -Dsonar.token=%SONAR_TOKEN%