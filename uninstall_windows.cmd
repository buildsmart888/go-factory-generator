@echo off
setlocal EnableExtensions
title GO Factory Generator Uninstaller

set "DEST=%APPDATA%\ingetrazo\plugins\go_factory_generator"

echo ==============================================
echo   GO Factory Generator - Uninstall
echo ==============================================
echo.

if not exist "%DEST%" (
  echo GO Factory Generator is not installed.
  pause
  exit /b 0
)

echo Removing:
echo   %DEST%
rmdir /S /Q "%DEST%"

if exist "%DEST%" (
  echo ERROR: Could not remove the plugin folder.
  pause
  exit /b 1
)

echo.
echo SUCCESS
echo GO Factory Generator has been removed.
echo Restart IngeTrazo if it is currently open.
echo.
pause
exit /b 0
