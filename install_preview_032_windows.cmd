@echo off
setlocal EnableExtensions EnableDelayedExpansion
title GO Factory Generator v0.3.2-preview / Shared Steel Catalog
set "ROOT=%~dp0"
set "PACK=%ROOT%dist\go_factory_generator-v0.3.2-preview.zip"
set "HASH=%PACK%.sha256"
set "DEST=%APPDATA%\ingetrazo\plugins\go_factory_generator"
set "STAGE=%TEMP%\go_factory_core_stage_%RANDOM%_%RANDOM%"
set "BACKUP=%LOCALAPPDATA%\GO Engineering\Backups\go_factory_%RANDOM%_%RANDOM%"
set "HAD_OLD=0"
set "GO_FACTORY_PACK=%PACK%"
set "GO_FACTORY_HASH=%HASH%"
set "GO_FACTORY_STAGE=%STAGE%"

echo =======================================================
echo GO Factory Generator v0.3.2-preview / GO Steel Catalog
echo Close IngeTrazo 0.5.9 completely before installation.
echo =======================================================
if not exist "%PACK%" goto missing
if not exist "%HASH%" goto missing
if exist "%DEST%\__init__.py" set "HAD_OLD=1"

echo [1/3] Verifying catalog-integrated preview ZIP...
powershell.exe -NoProfile -NonInteractive -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$want=(Get-Content -Raw -LiteralPath $env:GO_FACTORY_HASH).Trim().ToLowerInvariant();" ^
  "if($want -notmatch '^[0-9a-f]{64}$'){throw 'Invalid SHA-256 manifest'};" ^
  "$got=(Get-FileHash -Algorithm SHA256 -LiteralPath $env:GO_FACTORY_PACK).Hash.ToLowerInvariant();" ^
  "if($got -ne $want){throw 'Preview ZIP checksum mismatch'};" ^
  "Expand-Archive -LiteralPath $env:GO_FACTORY_PACK -DestinationPath $env:GO_FACTORY_STAGE -Force;" ^
  "$source=Join-Path $env:GO_FACTORY_STAGE 'go_factory_generator';" ^
  "foreach($name in @('__init__.py','engineering_core.py','steel_sections_v1.json')) {" ^
  " if(-not (Test-Path -LiteralPath (Join-Path $source $name) -PathType Leaf)) {throw ('Missing '+$name)}" ^
  "}"
if errorlevel 1 goto fail

echo [2/3] Backing up previous plugin...
if "%HAD_OLD%"=="1" (
  if not exist "%BACKUP%" mkdir "%BACKUP%"
  robocopy "%DEST%" "%BACKUP%" /E /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
  set "RC=!ERRORLEVEL!"
  if !RC! GEQ 8 (
    echo ERROR: Existing plugin backup failed. Original left untouched.
    goto fail
  )
)

echo [3/3] Installing GO Factory preview package...
if not exist "%DEST%" mkdir "%DEST%"
robocopy "%STAGE%\go_factory_generator" "%DEST%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
set "RC=!ERRORLEVEL!"
if !RC! GEQ 8 (
  echo ERROR: Plugin copy failed. Attempting rollback.
  if "%HAD_OLD%"=="1" (
    robocopy "%BACKUP%" "%DEST%" /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP >nul
  ) else (
    rmdir /S /Q "%DEST%" >nul 2>&1
  )
  goto fail
)
rmdir /S /Q "%STAGE%" >nul 2>&1
echo.
echo Installed: %DEST%
if "%HAD_OLD%"=="1" echo Previous version backed up under %BACKUP%
echo Restart IngeTrazo and generate Factory 01 again for tagged Core metadata.
echo NOTE: Section dimensions and kg/m remain NOMINAL/UNVERIFIED.
pause
exit /b 0

:missing
echo ERROR: Missing preview ZIP or matching SHA-256 file in dist.
pause
exit /b 1

:fail
rmdir /S /Q "%STAGE%" >nul 2>&1
echo FAILED. See messages above; backup if created: %BACKUP%
pause
exit /b 1
