@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════╗
echo ║         검키우기 매크로 빌드 스크립트                  ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM 이전 빌드 정리
echo [1/4] 이전 빌드 정리 중...
rmdir /s /q dist 2>nul
rmdir /s /q build\temp 2>nul

REM 의존성 설치 확인
echo [2/4] 의존성 확인 중...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
)

REM PyInstaller 실행
echo [3/4] EXE 빌드 중...
pyinstaller --clean --noconfirm ^
    --name "SwordMacro" ^
    --onefile ^
    --windowed ^
    --hidden-import "pynput.keyboard._win32" ^
    --hidden-import "pynput.mouse._win32" ^
    --exclude-module gymnasium ^
    --exclude-module stable_baselines3 ^
    --exclude-module tensorboard ^
    --exclude-module torch ^
    --distpath dist ^
    --workpath build\temp ^
    src\main_gui.py

echo.
echo [4/4] 빌드 결과 확인 중...
if exist "dist\SwordMacro.exe" (
    echo.
    echo ══════════════════════════════════════════════════════
    echo  ✓ 빌드 성공!
    echo  파일: dist\SwordMacro.exe
    for %%A in ("dist\SwordMacro.exe") do echo  크기: %%~zA bytes
    echo ══════════════════════════════════════════════════════
) else (
    echo.
    echo ══════════════════════════════════════════════════════
    echo  ✗ 빌드 실패
    echo  로그를 확인해주세요.
    echo ══════════════════════════════════════════════════════
    exit /b 1
)
