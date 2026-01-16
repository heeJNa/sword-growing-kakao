# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

카카오톡 "검키우기" 챗봇 게임 강화 매크로. pynput을 사용한 UI 자동화 기반으로, 채팅 메시지를 파싱하여 게임 상태를 추적하고 전략에 따라 강화/판매를 자동 실행합니다.

**대상 플랫폼**: Windows 10/11, macOS

## Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# GUI 실행
python -m src.main_gui

# CLI 실행
python -m src.main
python -m src.main --auto  # 자동 모드로 바로 시작

# 좌표 캘리브레이션
python -m src.main --calibrate

# 테스트
pytest tests/
pytest tests/test_parser.py -v  # 단일 테스트

# EXE 빌드 (Windows)
scripts\build.bat
```

## 플랫폼별 요구사항

### Windows
1. **Windows 10/11**: pynput 마우스/키보드 자동화
2. **카카오톡 실행**: 매크로 시작 전 카카오톡 채팅방 열어야 함

### macOS
1. **접근성 권한 필수**: pynput이 마우스/키보드를 제어하려면 접근성 권한 필요
   ```
   시스템 설정 → 개인정보 보호 및 보안 → 접근성
   → Terminal (또는 사용하는 터미널 앱) 체크
   ```
2. **카카오톡 Mac 버전**: 매크로 시작 전 카카오톡 채팅방 열어야 함
3. **Cmd 키 사용**: Mac에서는 Ctrl 대신 Cmd 키가 자동으로 사용됨

## Architecture

```
MacroRunner (core/macro.py) - 메인 오케스트레이터
    │
    ├── pynput (automation/) - 크로스플랫폼 마우스/키보드 자동화
    │
    ├── HotkeyListener (automation/hotkeys.py) - F1-F5 단축키 감지
    │
    ├── Parser (core/parser.py) - 채팅 메시지 → EnhanceResult (SUCCESS/MAINTAIN/DESTROY)
    │
    ├── Strategy (strategy/heuristic.py) - GameState → Action (ENHANCE/SELL/WAIT)
    │
    ├── Actions (core/actions.py) - enhance(), sell() → pynput
    │
    └── StatsCollector (stats/collector.py) - 레벨별 통계, 세션 기록
```

**데이터 흐름**: 채팅창 클릭 → Cmd/Ctrl+A+C → 클립보드 복사 → 정규식 파싱 → 상태 업데이트 → 전략 결정 → 입력창 클릭 → 타이핑 → Enter → 반복

## Key Design Decisions

- **pynput 사용**: 크로스플랫폼 마우스/키보드 자동화 (Mac/Windows 모두 지원)
- **플랫폼 자동 감지**: Mac에서는 Cmd, Windows에서는 Ctrl 키 자동 사용
- **직접 타이핑**: 클립보드 붙여넣기 대신 pynput.keyboard.type()으로 한글 직접 입력
- **쓰레드 분리**: 매크로 루프는 백그라운드 쓰레드, GUI는 메인 쓰레드 (tkinter 제약)

## Config Files

- `~/.sword-macro/settings.json` - 전략 파라미터, 딜레이 설정
- `~/.sword-macro/coordinates.json` - 채팅창 클릭 좌표
- `~/.sword-macro/stats/sessions/` - 세션별 통계 (JSON/CSV)

## Parser Patterns (core/parser.py)

```python
# 새 메시지 형식
RESULT_PATTERNS = {
    "success": r'〖\s*✨?\s*강화\s*성공\s*✨?\s*\+(\d+)\s*→\s*\+(\d+)\s*〗',
    "maintain": r'〖\s*💦?\s*강화\s*유지\s*💦?\s*〗',
    "destroy": r'〖\s*💥?\s*강화\s*파괴\s*💥?\s*〗',
    "sell": r'〖\s*검\s*판매\s*〗',
}
```

## 에러 처리

- **Mac 접근성 권한 오류**: pynput이 작동하지 않을 때
  - 해결: 시스템 설정 → 개인정보 보호 및 보안 → 접근성에서 터미널 앱 권한 부여
