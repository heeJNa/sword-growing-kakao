#!/bin/bash
# 검키우기 매크로 빌드 스크립트 (macOS/Linux)

echo "╔══════════════════════════════════════════════════════╗"
echo "║         검키우기 매크로 빌드 스크립트                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 플랫폼 감지
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    echo "플랫폼: macOS"
else
    PLATFORM="linux"
    echo "플랫폼: Linux"
fi

# 이전 빌드 정리
echo ""
echo "[1/4] 이전 빌드 정리 중..."
rm -rf dist build/temp SwordMacro.spec 2>/dev/null

# 의존성 설치 확인
echo "[2/4] 의존성 확인 중..."
if ! pip show pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller 설치 중..."
    pip install pyinstaller
fi

# PyInstaller 실행
echo "[3/4] 빌드 중..."

if [ "$PLATFORM" == "macos" ]; then
    # macOS: --onedir 모드로 .app 번들 생성
    pyinstaller --clean --noconfirm \
        --name "SwordMacro" \
        --onedir \
        --windowed \
        --hidden-import "pynput.keyboard._darwin" \
        --hidden-import "pynput.mouse._darwin" \
        --hidden-import "tkinter" \
        --hidden-import "_tkinter" \
        --collect-all "tkinter" \
        --exclude-module gymnasium \
        --exclude-module stable_baselines3 \
        --exclude-module tensorboard \
        --exclude-module torch \
        --distpath dist \
        --workpath build/temp \
        src/main_gui.py
else
    # Linux: --onefile 모드
    pyinstaller --clean --noconfirm \
        --name "SwordMacro" \
        --onefile \
        --hidden-import "pynput.keyboard._xorg" \
        --hidden-import "pynput.mouse._xorg" \
        --exclude-module gymnasium \
        --exclude-module stable_baselines3 \
        --exclude-module tensorboard \
        --exclude-module torch \
        --distpath dist \
        --workpath build/temp \
        src/main_gui.py
fi

echo ""
echo "[4/4] 빌드 결과 확인 중..."

if [ "$PLATFORM" == "macos" ]; then
    if [ -d "dist/SwordMacro.app" ]; then
        echo ""
        echo "══════════════════════════════════════════════════════"
        echo " ✓ 빌드 성공!"
        echo " 앱: dist/SwordMacro.app"
        echo ""
        echo " 실행 방법:"
        echo "   1. Finder에서 dist/SwordMacro.app 더블클릭"
        echo "   2. 또는 터미널에서: open dist/SwordMacro.app"
        echo ""
        echo " 주의: 손쉬운 사용 권한이 필요합니다."
        echo "   시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용"
        echo "   → SwordMacro 토글 ON"
        echo "══════════════════════════════════════════════════════"
    else
        echo ""
        echo "══════════════════════════════════════════════════════"
        echo " ✗ 빌드 실패"
        echo " 로그를 확인해주세요."
        echo "══════════════════════════════════════════════════════"
        exit 1
    fi
else
    if [ -f "dist/SwordMacro" ]; then
        echo ""
        echo "══════════════════════════════════════════════════════"
        echo " ✓ 빌드 성공!"
        echo " 파일: dist/SwordMacro"
        echo " 크기: $(du -h dist/SwordMacro | cut -f1)"
        echo ""
        echo " 실행 방법: ./dist/SwordMacro"
        echo "══════════════════════════════════════════════════════"
    else
        echo ""
        echo "══════════════════════════════════════════════════════"
        echo " ✗ 빌드 실패"
        echo " 로그를 확인해주세요."
        echo "══════════════════════════════════════════════════════"
        exit 1
    fi
fi
