@echo off
chcp 65001 > nul

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 ( py -3 main.py & exit /b )

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 ( python main.py & exit /b )

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 ( python3 main.py & exit /b )

echo Python が見つかりません。setup.bat を先に実行してください。
pause
