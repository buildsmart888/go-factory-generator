@echo off
setlocal EnableExtensions
title GO Factory v0.3.2-preview - Core catalog and plugin packaging
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "LOG=%ROOT%go-core-v01-qa.log"
echo GO Factory v0.3.2-preview — catalog tests and plugin package
py -3.11 -m compileall -q go_factory_generator > "%LOG%" 2>&1
if errorlevel 1 goto fail
py -3.11 -m unittest discover -s tests -p "test_engineering_core.py" -v >> "%LOG%" 2>&1
if errorlevel 1 goto fail
py -3.11 -m unittest discover -s tests -p "test_factory_catalog_parity.py" -v >> "%LOG%" 2>&1
if errorlevel 1 goto fail
py -3.11 scripts\package_preview_032.py >> "%LOG%" 2>&1
if errorlevel 1 goto fail
echo PASS: GO Factory section catalog parity, nominal core unit tests and ZIP checksum.
echo Preview ZIP: dist\go_factory_generator-v0.3.2-preview.zip
echo Hash: dist\go_factory_generator-v0.3.2-preview.zip.sha256
echo NOTE: Real IngeTrazo 0.5.9 GUI verification still required.
pause
exit /b 0
:fail
echo FAIL: GO Factory Core preview QA.
powershell.exe -NoProfile -NonInteractive -Command "Get-Content -LiteralPath $env:LOG -Tail 75"
pause
exit /b 1
