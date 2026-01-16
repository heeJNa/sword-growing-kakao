#!/bin/bash
# 검키우기 매크로 빌드 스크립트 (macOS/Linux)

echo "╔══════════════════════════════════════════════════════╗"
echo "║         검키우기 매크로 빌드 스크립트                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 이전 빌드 정리
echo "[1/4] 이전 빌드 정리 중..."
rm -rf dist build/temp 2>/dev/null

# 의존성 설치 확인
echo "[2/4] 의존성 확인 중..."
if ! pip show pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller 설치 중..."
    pip install pyinstaller
fi

# PyInstaller 실행
echo "[3/4] 빌드 중..."
pyinstaller --clean --noconfirm \
    --name "SwordMacro" \
    --onefile \
    --windowed \
    --hidden-import "pynput.keyboard._darwin" \
    --hidden-import "pynput.mouse._darwin" \
    --exclude-module gymnasium \
    --exclude-module stable_baselines3 \
    --exclude-module tensorboard \
    --exclude-module torch \
    --distpath dist \
    --workpath build/temp \
    src/main_gui.py

echo ""
echo "[4/4] 빌드 결과 확인 중..."

if [ -f "dist/SwordMacro" ] || [ -d "dist/SwordMacro.app" ]; then
    echo ""
    echo "══════════════════════════════════════════════════════"
    echo " ✓ 빌드 성공!"
    if [ -f "dist/SwordMacro" ]; then
        echo " 파일: dist/SwordMacro"
        echo " 크기: $(du -h dist/SwordMacro | cut -f1)"
    fi
    if [ -d "dist/SwordMacro.app" ]; then
        echo " 앱: dist/SwordMacro.app"
    fi
    echo "══════════════════════════════════════════════════════"
else
    echo ""
    echo "══════════════════════════════════════════════════════"
    echo " ✗ 빌드 실패"
    echo " 로그를 확인해주세요."
    echo "══════════════════════════════════════════════════════"
    exit 1
fi
