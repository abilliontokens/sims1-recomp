@echo off
set "GAME_EXE=Sims1"
cd /d "%~dp0"
set "OUT=out\build\release"
if not exist "%OUT%\%GAME_EXE%.exe" call build.bat || exit /b 1
rem the configure step writes where the SDK is
if not exist "%OUT%\sdk_dir.txt" cmake --preset release >nul || exit /b 1
if not exist "%OUT%\sdk_dir.txt" echo %OUT%\sdk_dir.txt was not written, update the SDK. && exit /b 1
set /p SDK=<out\build\release\sdk_dir.txt
del /q "%GAME_EXE%-win64.zip" 2>nul
rem an empty assets folder beside the exe, where the game (files or .iso) goes
rd /s /q "%OUT%\release" 2>nul
mkdir "%OUT%\release\assets"
rem 7z is not on PATH in a default install
set "SEVENZIP=7z"
where 7z >nul 2>nul || set "SEVENZIP=%ProgramFiles%\7-Zip\7z.exe"
if not exist "%SEVENZIP%" if "%SEVENZIP%" neq "7z" echo 7-Zip was not found. Install it or put 7z.exe on PATH. && exit /b 1
"%SEVENZIP%" a "%GAME_EXE%-win64.zip" ".\%OUT%\%GAME_EXE%.exe" ".\%OUT%\release\assets" .\README.md "%SDK%\THIRD_PARTY.txt"
