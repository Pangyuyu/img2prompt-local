@echo off
chcp 65001 >nul
echo ========================================
echo   Image Description Tool - Build EXE
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [1/4] Checking Python environment...
echo.

:: Clean old files
echo [2/4] Cleaning old files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del /q main.spec
echo Cleaned.
echo.

:: Install dependencies
echo [3/4] Installing dependencies...
pip install -q -r requirements.txt
pip install -q pyinstaller
echo Dependencies installed.
echo.

:: Build
echo [4/4] Building EXE (may take 1-3 minutes)...
echo.

pyinstaller --name="ImageDescriber" ^
            --windowed ^
            --onefile ^
            --add-data "README.md;." ^
            --hidden-import customtkinter ^
            --hidden-import PIL ^
            --hidden-import requests ^
            --hidden-import PIL.Image ^
            --hidden-import PIL.ImageTk ^
            main.py

echo.
echo ========================================
if exist "dist\ImageDescriber.exe" (
    echo SUCCESS!
    echo.
    echo EXE location:
    echo    dist\ImageDescriber.exe
    echo.
    echo File size:
    dir "dist\ImageDescriber.exe"
) else (
    echo FAILED!
    echo Please check error messages above.
)
echo ========================================
echo.
pause
