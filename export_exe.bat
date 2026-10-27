@echo off
title Build DJOP_DEMO Exe
echo ========================================================
echo   Building DJOP_DEMO.exe with PyInstaller
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Running PyInstaller...
pyinstaller DJOP_DEMO.spec --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Setting up required resource folders...
xcopy /E /I /Y "assets" "dist\DJOP_DEMO\assets"
xcopy /E /I /Y "data" "dist\DJOP_DEMO\data"
xcopy /E /I /Y "voices" "dist\DJOP_DEMO\voices"
if not exist "dist\DJOP_DEMO\ffmpeg" (
    if exist "C:\ffmpeg" xcopy /E /I /Y "C:\ffmpeg" "dist\DJOP_DEMO\ffmpeg"
)
if not exist "dist\DJOP_DEMO\_internal\ssg\artifacts" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python310\Lib\site-packages\ssg" (
        xcopy /E /I /Y "%LOCALAPPDATA%\Programs\Python\Python310\Lib\site-packages\ssg" "dist\DJOP_DEMO\_internal\ssg\"
    )
)

if not exist "dist\DJOP_DEMO\models_cache" (
    echo Creating models_cache junction link...
    mklink /J "dist\DJOP_DEMO\models_cache" "%~dp0models_cache"
)

echo.
echo [3/3] Build completed successfully!
echo Executable location: "%~dp0dist\DJOP_DEMO\DJOP_DEMO.exe"
echo ========================================================
pause
