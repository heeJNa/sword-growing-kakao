# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

카카오톡 "검키우기" 챗봇 게임 강화 매크로. pyautogui/pynput을 사용한 UI 자동화 기반으로, 채팅 메시지를 파싱하여 게임 상태를 추적하고 전략에 따라 강화/판매를 자동 실행합니다.

**대상 플랫폼**: Windows 10/11 (별도 기기에서 실행)

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

# 빌드 (macOS/Linux)
./scripts/build.sh
```

## Architecture

```
MacroRunner (core/macro.py) - 메인 오케스트레이터
    │
    ├── HotkeyListener (automation/hotkeys.py) - F1-F5 단축키 감지
    │
    ├── Parser (core/parser.py) - 채팅 메시지 → EnhanceResult (SUCCESS/MAINTAIN/DESTROY)
    │
    ├── Strategy (strategy/heuristic.py) - GameState → Action (ENHANCE/SELL/WAIT)
    │
    ├── Actions (core/actions.py) - enhance(), sell() → clipboard + pyautogui
    │
    └── StatsCollector (stats/collector.py) - 레벨별 통계, 세션 기록
```

**데이터 흐름**: 채팅 복사(Ctrl+A/C) → 정규식 파싱 → 상태 업데이트 → 전략 결정 → 클립보드 입력(Ctrl+V) → 반복

## Key Design Decisions

- **클립보드 방식 한글 입력**: pyautogui.write()가 한글을 지원하지 않아 pyperclip + Ctrl+V 사용
- **절대 좌표 기반**: 창 핸들이 아닌 화면 좌표 클릭 (Windows 배율 100% 필수)
- **쓰레드 분리**: 매크로 루프는 백그라운드 쓰레드, GUI는 메인 쓰레드 (tkinter 제약)
- **Queue 기반 통신**: 매크로 쓰레드 → GUI 쓰레드 업데이트

## Config Files

- `~/.sword-macro/settings.json` - 전략 파라미터, 딜레이 설정
- `~/.sword-macro/coordinates.json` - 채팅창 클릭 좌표
- `~/.sword-macro/stats/sessions/` - 세션별 통계 (JSON/CSV)

## Parser Patterns (core/parser.py)

```python
# 우선순위: destroy > success > maintain
destroy: r'파괴|부서|0강.*시작'
success: r'\+(\d+)강.*성공'
maintain: r'실패.*유지|레벨.*유지'
gold: r'(\d{1,3}(?:,\d{3})*)\s*(골드|원|G)'
```
