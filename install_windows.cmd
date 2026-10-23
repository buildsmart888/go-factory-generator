@echo off
setlocal EnableExtensions EnableDelayedExpansion
title GO Factory Generator Installer

echo ==============================================
echo   GO Factory Generator v0.2.3 - IngeTrazo
echo ==============================================
echo.

set "SRC=%~dp0go_factory_generator"
set "DEST=%APPDATA%\ingetrazo\plugins\go_factory_generator"
set "BACKUPROOT=%APPDATA%\ingetrazo\go_factory_backups"

if not exist "%SRC%\__init__.py" (
  echo ERROR: Plugin source not found:
  echo   %SRC%
  echo.
  echo Run this installer from the repository root.
  pause
  exit /b 1
)

if not exist "%APPDATA%\ingetrazo\plugins" (
  mkdir "%APPDATA%\ingetrazo\plugins" >nul 2>&1
)

if not exist "%BACKUPROOT%" (
  mkdir "%BACKUPROOT%" >nul 2>&1
)

if exist "%DEST%" (
  for /f "tokens=1-4 delims=/ " %%a in ("%date%") do (
    set "D=%%d%%b%%c"
  )
  set "T=%time: =0%"
  set "T=%T::=%"
  set "T=%T:.=%"
  set "BACKUP=%BACKUPROOT%\go_factory_generator_backup_%D%_%T%"

  echo Existing installation found.
  echo Backing up to:
  echo   !BACKUP!
  xcopy "%DEST%" "!BACKUP!\" /E /I /H /Y >nul
)

echo Installing plugin...
robocopy "%SRC%" "%DEST%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
set "RC=%ERRORLEVEL%"

if %RC% GEQ 8 (
  echo.
  echo ERROR: Installation failed. Robocopy exit code: %RC%
  pause
  exit /b %RC%
)

echo.
echo SUCCESS
echo Installed to:
echo   %DEST%
echo.
echo Next:
echo   1. Close IngeTrazo completely
echo   2. Reopen IngeTrazo
echo   3. Look for the GO Factory toolbar
echo.
pause
exit /b 0
