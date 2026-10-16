@echo off
chcp 65001 > nul
echo ========================================
echo  自動文字起こし セットアップ
echo ========================================
echo.

REM Python チェック
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py -3
    goto :found
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
    goto :found
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python3
    goto :found
)

echo [エラー] Python が見つかりません。
echo https://www.python.org/downloads/ からインストールしてください。
echo インストール時に "Add Python to PATH" にチェックを入れてください。
pause
exit /b 1

:found
echo Python が見つかりました: %PYTHON%
%PYTHON% --version

echo.
echo 依存ライブラリをインストール中...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install PyQt6 faster-whisper requests beautifulsoup4

echo.
echo ========================================
echo  セットアップ完了！
echo  run.bat で起動できます。
echo ========================================
pause
