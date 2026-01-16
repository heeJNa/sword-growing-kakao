# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

카카오톡 "검키우기" 챗봇 게임 강화 매크로. Win32 API를 사용한 UI 자동화 기반으로, 채팅 메시지를 파싱하여 게임 상태를 추적하고 전략에 따라 강화/판매를 자동 실행합니다.

**대상 플랫폼**: Windows 10/11 (RDP 원격 접속 지원)

## Commands

```bash
# 의존성 설치 (Windows)
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

## 필수 요구사항

1. **Windows 10/11**: Win32 API 사용으로 Windows 전용
2. **pywin32**: RDP 환경에서도 동작하는 Win32 API 지원
3. **카카오톡 실행**: 매크로 시작 전 카카오톡 채팅방 열어야 함

```bash
# pywin32 설치 (자동 설치됨, 수동 설치 시)
pip install pywin32
```

## Architecture

```
MacroRunner (core/macro.py) - 메인 오케스트레이터
    │
    ├── Win32Window (automation/win32_automation.py) - 창 핸들 기반 자동화
    │
    ├── WindowFinder - 카카오톡 창 자동 탐색
    │
    ├── HotkeyListener (automation/hotkeys.py) - F1-F5 단축키 감지
    │
    ├── Parser (core/parser.py) - 채팅 메시지 → EnhanceResult (SUCCESS/MAINTAIN/DESTROY)
    │
    ├── Strategy (strategy/heuristic.py) - GameState → Action (ENHANCE/SELL/WAIT)
    │
    ├── Actions (core/actions.py) - enhance(), sell() → Win32 API
    │
    └── StatsCollector (stats/collector.py) - 레벨별 통계, 세션 기록
```

**데이터 흐름**: 창 탐색 → 채팅 복사(PostMessage) → 정규식 파싱 → 상태 업데이트 → 전략 결정 → 클립보드 입력(SendMessage) → 반복

## Key Design Decisions

- **Win32 API 사용**: RDP 환경에서도 동작 (PostMessage/SendMessage로 창에 직접 메시지 전송)
- **창 핸들 기반**: 화면 좌표를 클라이언트 좌표로 변환하여 창에 전송
- **클립보드 방식 한글 입력**: win32clipboard API로 한글 텍스트 입력
- **쓰레드 분리**: 매크로 루프는 백그라운드 쓰레드, GUI는 메인 쓰레드 (tkinter 제약)
- **자동 창 탐색**: "카카오톡", "KakaoTalk", "검키우기" 제목으로 창 자동 탐색

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

- **KakaoWindowNotFoundError**: 카카오톡 창을 찾지 못할 때 발생
  - 해결: 카카오톡 실행 후 채팅방 열기
  - 로그에 현재 열린 창 목록 출력됨
