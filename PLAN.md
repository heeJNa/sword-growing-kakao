# 카카오톡 "검키우기" 챗봇 게임 강화 매크로 구현 계획

## 목차
1. [기술 스택 선택 및 근거](#1-기술-스택-선택-및-근거)
2. [프로젝트 구조 설계](#2-프로젝트-구조-설계)
3. [핵심 기능 및 우선순위](#3-핵심-기능-및-우선순위)
   - Phase 1: 기본 매크로 (MVP)
   - Phase 2: 규칙 기반 전략
   - Phase 3: AI 기반 전략 (선택)
   - Phase 4: 통계 시스템
   - Phase 5: GUI 대시보드
   - Phase 6: EXE 배포 및 문서화
4. [단계별 구현 작업](#4-단계별-구현-작업)
5. [테스트 및 검증 방법](#5-테스트-및-검증-방법)
6. [위험 요소 및 대응](#6-위험-요소-및-대응)

---

## 1. 기술 스택 선택 및 근거

### 1.1 언어 선택: Python

| 기준 | Python | Node.js |
|------|--------|---------|
| **GUI 자동화 라이브러리** | pywin32 (Win32 API), pynput (성숙함) | robotjs (제한적) |
| **강화학습 생태계** | stable-baselines3, gymnasium (풍부) | 거의 없음 |
| **참고 레포지토리 호환성** | 직접 활용 가능 | 재작성 필요 |
| **Windows 지원** | 우수 (Win32 API 연동, RDP 호환) | 보통 |
| **클립보드 처리** | win32clipboard (RDP 호환) | 추가 설정 필요 |
| **데이터 분석** | pandas, numpy (표준) | 제한적 |

**결론**: Python 3.11+ 선택 (참고 레포지토리와 동일)

**대상 플랫폼**: Windows 10/11 (별도 기기에서 실행)

### 1.2 필요 라이브러리 목록

#### 핵심 의존성
```
# 자동화 (Win32 API - RDP 호환)
pywin32>=306           # Win32 API (마우스/키보드/클립보드)
pynput>=1.7.6          # 입력 감지 및 단축키 처리

# 데이터 처리
pandas>=2.0.0          # 데이터 분석/CSV 처리
numpy>=1.24.0          # 수치 연산

# GUI & 시각화 (Phase 4-5)
matplotlib>=3.8.0      # 차트 시각화
# tkinter는 Python 내장 (별도 설치 불필요)

# 강화학습 (Phase 3)
gymnasium>=0.29.0      # RL 환경 프레임워크
stable-baselines3>=2.0.0  # PPO 알고리즘
sb3-contrib>=2.0.0     # Maskable PPO
tensorboard>=2.14.0    # 학습 모니터링

# 개발 도구
pytest>=7.4.0          # 테스트
black>=23.0.0          # 코드 포맷팅
mypy>=1.5.0            # 타입 체크
```

### 1.3 패키지 관리: uv

참고 레포지토리와 동일하게 `uv` 사용 (pip보다 10-100배 빠름)

```bash
# 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 초기화
uv init
uv add pywin32 pynput pandas numpy matplotlib
```

---

## 2. 프로젝트 구조 설계

### 2.1 디렉토리 구조

```
sword-growing-kakao/
├── pyproject.toml           # 프로젝트 메타데이터 및 의존성
├── requirements.txt         # pip 호환 의존성
├── uv.lock                  # uv 락 파일
├── README.md                # 프로젝트 문서
├── Makefile                 # 빌드/실행 스크립트
│
├── src/
│   ├── __init__.py
│   ├── main.py              # 진입점 (CLI 매크로 실행)
│   ├── main_gui.py          # 진입점 (GUI 모드)
│   │
│   ├── core/                # 핵심 로직
│   │   ├── __init__.py
│   │   ├── macro.py         # 매크로 메인 루프
│   │   ├── actions.py       # 게임 행동 (강화, 판매 등)
│   │   ├── parser.py        # 채팅 메시지 파싱
│   │   └── state.py         # 게임 상태 관리
│   │
│   ├── automation/          # 자동화 모듈
│   │   ├── __init__.py
│   │   ├── keyboard.py      # 키보드 제어
│   │   ├── mouse.py         # 마우스 제어
│   │   ├── clipboard.py     # 클립보드 처리
│   │   └── hotkeys.py       # 단축키 리스너
│   │
│   ├── strategy/            # 전략 모듈
│   │   ├── __init__.py
│   │   ├── base.py          # 전략 인터페이스
│   │   ├── heuristic.py     # 규칙 기반 전략
│   │   └── ai.py            # AI 기반 전략 (Phase 3)
│   │
│   ├── stats/               # 통계 시스템 (Phase 4)
│   │   ├── __init__.py
│   │   ├── models.py        # 통계 데이터 클래스
│   │   ├── collector.py     # 실시간 통계 수집
│   │   ├── storage.py       # 파일 저장/로드
│   │   └── analysis.py      # 수익률 분석
│   │
│   ├── gui/                 # GUI 대시보드 (Phase 5)
│   │   ├── __init__.py
│   │   ├── app.py           # 메인 애플리케이션
│   │   ├── updater.py       # 실시간 업데이트 로직
│   │   │
│   │   ├── widgets/         # UI 위젯
│   │   │   ├── __init__.py
│   │   │   ├── status_panel.py    # 현재 상태 패널
│   │   │   ├── stats_panel.py     # 세션 통계 패널
│   │   │   ├── log_panel.py       # 로그 패널
│   │   │   └── control_panel.py   # 제어 버튼 패널
│   │   │
│   │   ├── charts/          # 차트 컴포넌트
│   │   │   ├── __init__.py
│   │   │   ├── bar_chart.py       # 레벨별 확률 차트
│   │   │   └── line_chart.py      # 골드 추이 차트
│   │   │
│   │   └── dialogs/         # 다이얼로그
│   │       ├── __init__.py
│   │       └── settings_dialog.py # 설정 창
│   │
│   ├── rl/                  # 강화학습 (Phase 3)
│   │   ├── __init__.py
│   │   ├── env.py           # Gymnasium 환경
│   │   ├── train.py         # 학습 스크립트
│   │   ├── inference.py     # 추론 모듈
│   │   └── rewards.py       # 보상 함수
│   │
│   └── config/              # 설정
│       ├── __init__.py
│       ├── settings.py      # 전역 설정
│       ├── coordinates.py   # 화면 좌표
│       └── game_data.py     # 게임 데이터 (확률, 가격)
│
├── models/                  # 학습된 모델 저장
│   ├── checkpoints/
│   └── final/
│
├── data/                    # 데이터 파일
│   ├── stats/               # 통계 데이터
│   │   └── sessions/        # 세션별 통계 파일
│   ├── level_summary.csv    # 레벨별 통계
│   └── logs/                # 실행 로그
│
├── tests/                   # 테스트 코드
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_actions.py
│   ├── test_strategy.py
│   ├── test_stats.py        # 통계 테스트
│   └── test_env.py
│
└── scripts/                 # 유틸리티 스크립트
    ├── calibrate.py         # 좌표 캘리브레이션
    └── collect_data.py      # 데이터 수집
```

### 2.2 파일별 역할 상세

| 파일 | 역할 | 주요 클래스/함수 |
|------|------|------------------|
| `src/main.py` | 프로그램 진입점 | `main()`, CLI 인자 처리 |
| `src/core/macro.py` | 매크로 메인 루프 | `MacroRunner`, `worker_loop()` |
| `src/core/actions.py` | 게임 행동 실행 | `enhance()`, `sell()`, `buy_item()` |
| `src/core/parser.py` | 채팅 파싱 | `parse_enhance_result()`, `parse_gold()` |
| `src/core/state.py` | 상태 관리 | `GameState` dataclass |
| `src/automation/keyboard.py` | 키보드 제어 | `type_text()`, `press_key()` |
| `src/automation/mouse.py` | 마우스 제어 | `click()`, `move_to()` |
| `src/automation/clipboard.py` | 클립보드 | `copy_chat()`, `get_text()` |
| `src/automation/hotkeys.py` | 단축키 | `HotkeyListener` |
| `src/strategy/base.py` | 전략 인터페이스 | `Strategy` ABC |
| `src/strategy/heuristic.py` | 규칙 전략 | `HeuristicStrategy` |
| `src/config/settings.py` | 설정값 | 타임아웃, 딜레이 상수 |
| `src/config/coordinates.py` | 화면 좌표 | `CHAT_OUTPUT`, `CHAT_INPUT` |
| `src/config/game_data.py` | 게임 데이터 | 강화 확률, 판매가 테이블 |

---

## 3. 핵심 기능 및 우선순위

### 3.1 Phase 1: 기본 매크로 (MVP)

**목표**: 수동 단축키로 강화/판매 명령 실행

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| 좌표 설정 | P0 | 채팅창 위치 설정 |
| 강화 명령 실행 | P0 | `/ㄱ` 입력 자동화 |
| 판매 명령 실행 | P0 | `/판` 입력 자동화 |
| 단축키 리스너 | P0 | F1-F5 키 감지 |
| 채팅 메시지 파싱 | P1 | 강화 결과 인식 |
| 현재 상태 표시 | P1 | 레벨, 골드 출력 |

### 3.2 Phase 2: 목표 레벨 강화 전략

**목표**: 설정한 목표 레벨까지 자동으로 계속 강화

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| 자동 루프 | P0 | 목표까지 연속 강화 실행 |
| 목표 레벨 설정 | P0 | 원하는 강화 등급 지정 |
| 파괴 시 재시작 | P0 | 0강에서 자동으로 다시 강화 |
| 목표 도달 일시정지 | P1 | 목표 레벨 도달 시 알림 |
| 자금 부족 처리 | P1 | 골드 부족 시 판매 또는 대기 |
| 방지권 사용 | P2 | 고레벨 강화 시 자동 사용 |

**전략 동작 방식:**
```
시작 (0강) → 강화 → 성공/유지/파괴
                    ↓
            성공: 레벨 +1 → 목표 도달? → 일시정지
            유지: 레벨 유지 → 계속 강화
            파괴: 0강으로 → 처음부터 다시 강화
```

**전략 설정 항목:**
| 항목 | 기본값 | 설명 |
|------|--------|------|
| target_level | 15 | 목표 강화 레벨 |
| sell_on_target | false | 목표 도달 시 판매 여부 |
| pause_on_target | true | 목표 도달 시 일시정지 |
| min_gold | 1000 | 최소 보유 골드 (이하면 판매) |

### 3.3 Phase 3: AI 기반 전략 (선택)

**목표**: 강화학습으로 최적 전략 도출

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| Gymnasium 환경 | P0 | 게임 시뮬레이션 |
| PPO 모델 학습 | P0 | Maskable PPO 훈련 |
| 모델 추론 | P0 | 실시간 의사결정 |
| 학습 모니터링 | P1 | TensorBoard 연동 |
| 하이퍼파라미터 튜닝 | P2 | 성능 최적화 |

### 3.4 Phase 4: 통계 시스템

**목표**: 강화 결과를 레벨별로 수집하고 분석

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| 결과 기록 | P0 | 성공/유지/파괴 횟수 저장 |
| 레벨별 통계 | P0 | 각 레벨의 실제 확률 계산 |
| 세션 통계 | P0 | 현재 세션의 요약 정보 |
| 누적 통계 | P1 | 전체 기간 통계 (CSV 저장) |
| 수익률 분석 | P1 | 순이익, ROI 계산 |
| 통계 내보내기 | P2 | JSON/CSV 파일 출력 |

### 3.5 Phase 5: GUI 대시보드

**목표**: 실시간 매크로 현황 모니터링 인터페이스

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| 메인 대시보드 | P0 | 현재 상태 실시간 표시 |
| 레벨별 확률 차트 | P0 | 막대 그래프로 시각화 |
| 세션 히스토리 | P0 | 최근 강화 결과 로그 |
| 통계 패널 | P0 | 성공률, 수익률 표시 |
| 설정 패널 | P1 | 전략 파라미터 조정 |
| 시작/정지 버튼 | P1 | GUI에서 매크로 제어 |
| 실시간 그래프 | P2 | 골드 변화 추이 차트 |
| System Tray | P1 | 창 닫으면 백그라운드 실행 |
| 트레이 알림 | P2 | 목표 도달 시 알림 표시 |

### 3.6 Phase 6: EXE 배포 패키지 및 사용법 문서

**목표**: Python 미설치 환경에서도 실행 가능한 단일 EXE 파일 생성 및 사용법 문서 제공

| 기능 | 우선순위 | 설명 |
|------|----------|------|
| PyInstaller 패키징 | P0 | 단일 EXE 파일 생성 |
| 아이콘 적용 | P1 | 커스텀 앱 아이콘 |
| 버전 정보 포함 | P1 | Windows 파일 속성에 버전 표시 |
| 사용법 문서 | P0 | README 및 빠른 시작 가이드 |
| 설치 가이드 | P0 | 단계별 설치 안내 |
| FAQ 문서 | P1 | 자주 묻는 질문 모음 |
| 문제 해결 가이드 | P1 | 일반적인 오류 해결 방법 |
| 자동 업데이트 체크 | P2 | GitHub 릴리즈 확인 |

---

## 4. 단계별 구현 작업

### 4.1 Phase 1 상세 작업

#### Task 1.1: 프로젝트 초기화
- pyproject.toml 생성
- 의존성 설치 (uv add ...)
- 디렉토리 구조 생성
- .gitignore 설정

#### Task 1.2: 자동화 모듈 구현
- keyboard.py: 키보드 제어 함수
- mouse.py: 마우스 제어 함수
- clipboard.py: 클립보드 조작

#### Task 1.3: 게임 행동 구현
- actions.py: enhance(), sell() 함수

#### Task 1.4: 채팅 파싱 구현
- parser.py: 정규식 기반 메시지 파싱

#### Task 1.5: 단축키 리스너 구현
- hotkeys.py: HotkeyListener 클래스

#### Task 1.6: 메인 실행 루프
- main.py: CLI 진입점

### 4.2 Phase 2 상세 작업

#### Task 2.1: 전략 인터페이스 정의
- base.py: Strategy ABC, Action enum

#### Task 2.2: 목표 강화 전략 구현
- heuristic.py: EnhanceUntilTargetStrategy 클래스
- 프리셋 전략: 안전 강화 (10강), 목표 강화 (15강), 최고 강화 (20강)

#### Task 2.3: 자동 루프 구현
- macro.py: MacroRunner 클래스

### 4.3 Phase 3 상세 작업 (선택)

#### Task 3.1: Gymnasium 환경 구현
- env.py: SwordEnhanceEnv 클래스

#### Task 3.2: PPO 학습 스크립트
- train.py: 학습 파이프라인

### 4.4 Phase 4 상세 작업 (통계 시스템)

#### Task 4.1: 통계 데이터 구조 설계
- `src/stats/models.py`: 통계 데이터 클래스 정의

```python
@dataclass
class LevelStats:
    level: int
    success_count: int = 0
    maintain_count: int = 0
    destroy_count: int = 0
    total_attempts: int = 0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total_attempts if self.total_attempts > 0 else 0

    @property
    def maintain_rate(self) -> float:
        return self.maintain_count / self.total_attempts if self.total_attempts > 0 else 0

    @property
    def destroy_rate(self) -> float:
        return self.destroy_count / self.total_attempts if self.total_attempts > 0 else 0

@dataclass
class SessionStats:
    start_time: datetime
    total_enhances: int = 0
    total_sells: int = 0
    starting_gold: int = 0
    current_gold: int = 0
    max_level_reached: int = 0
    level_stats: Dict[int, LevelStats] = field(default_factory=dict)
```

#### Task 4.2: 통계 수집기 구현
- `src/stats/collector.py`: 실시간 통계 수집 클래스

```python
class StatsCollector:
    def __init__(self):
        self.session_stats = SessionStats(start_time=datetime.now())
        self.history: List[EnhanceRecord] = []

    def record_enhance(self, level: int, result: EnhanceResult) -> None:
        """강화 결과 기록"""
        if level not in self.session_stats.level_stats:
            self.session_stats.level_stats[level] = LevelStats(level=level)

        stats = self.session_stats.level_stats[level]
        stats.total_attempts += 1

        if result == EnhanceResult.SUCCESS:
            stats.success_count += 1
        elif result == EnhanceResult.MAINTAIN:
            stats.maintain_count += 1
        elif result == EnhanceResult.DESTROY:
            stats.destroy_count += 1

    def get_level_summary(self) -> pd.DataFrame:
        """레벨별 통계 DataFrame 반환"""
        ...

    def export_csv(self, path: str) -> None:
        """CSV 파일로 내보내기"""
        ...
```

#### Task 4.3: 통계 저장소 구현
- `src/stats/storage.py`: 파일 기반 통계 저장
- JSON/CSV 형식 지원
- 세션별 파일 분리

#### Task 4.4: 수익률 분석 모듈
- `src/stats/analysis.py`: 수익 분석 함수

```python
def calculate_profit(session: SessionStats) -> Dict:
    """세션 수익률 계산"""
    return {
        "gross_profit": session.current_gold - session.starting_gold,
        "roi": (session.current_gold - session.starting_gold) / session.starting_gold * 100,
        "profit_per_enhance": ...,
        "best_level": ...,
    }
```

### 4.5 Phase 5 상세 작업 (GUI 대시보드)

#### Task 5.1: GUI 프레임워크 선택
- **Tkinter** 선택 (Python 내장, 설치 불필요)
- matplotlib 연동으로 차트 표시
- 실시간 업데이트 지원

#### Task 5.2: 메인 윈도우 레이아웃
- `src/gui/app.py`: 메인 애플리케이션 클래스

```
┌──────────────────────────────────────────────────────────────┐
│                    검키우기 매크로 대시보드                      │
├─────────────────────┬────────────────────────────────────────┤
│   현재 상태 패널     │              차트 영역                   │
│  ┌───────────────┐  │  ┌──────────────────────────────────┐  │
│  │ 레벨: +12강   │  │  │     레벨별 강화 성공률 차트         │  │
│  │ 골드: 500,000 │  │  │     (막대 그래프)                  │  │
│  │ 상태: 실행중   │  │  │                                   │  │
│  └───────────────┘  │  │  ■ 성공  ■ 유지  ■ 파괴           │  │
│                     │  └──────────────────────────────────┘  │
│   세션 통계 패널     │                                        │
│  ┌───────────────┐  │  ┌──────────────────────────────────┐  │
│  │ 총 강화: 150  │  │  │        골드 변화 추이 그래프        │  │
│  │ 성공률: 65%   │  │  │        (선 그래프)                 │  │
│  │ 수익: +50,000 │  │  └──────────────────────────────────┘  │
│  └───────────────┘  │                                        │
├─────────────────────┴────────────────────────────────────────┤
│                       최근 기록 로그                           │
│  12:00:01 | +10강 → +11강 | 성공                              │
│  12:00:03 | +11강 → +11강 | 유지                              │
│  12:00:05 | +11강 → 0강   | 파괴                              │
├──────────────────────────────────────────────────────────────┤
│  [▶ 시작]  [■ 정지]  [⚙ 설정]  [📊 통계 내보내기]              │
└──────────────────────────────────────────────────────────────┘
```

#### Task 5.3: 위젯 구현
- `src/gui/widgets/status_panel.py`: 현재 상태 표시 패널
- `src/gui/widgets/stats_panel.py`: 세션 통계 패널
- `src/gui/widgets/chart_panel.py`: 차트 패널 (matplotlib)
- `src/gui/widgets/log_panel.py`: 로그 목록 패널
- `src/gui/widgets/control_panel.py`: 제어 버튼 패널

#### Task 5.4: 차트 컴포넌트 구현
- `src/gui/charts/bar_chart.py`: 레벨별 확률 막대 차트
- `src/gui/charts/line_chart.py`: 골드 추이 선 차트

```python
class LevelProbabilityChart:
    """레벨별 성공/유지/파괴 확률 막대 차트"""
    def __init__(self, parent: tk.Frame):
        self.figure = Figure(figsize=(6, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, parent)

    def update(self, stats: Dict[int, LevelStats]) -> None:
        """차트 데이터 업데이트"""
        self.ax.clear()
        levels = sorted(stats.keys())
        success_rates = [stats[l].success_rate for l in levels]
        maintain_rates = [stats[l].maintain_rate for l in levels]
        destroy_rates = [stats[l].destroy_rate for l in levels]

        x = np.arange(len(levels))
        width = 0.25

        self.ax.bar(x - width, success_rates, width, label='성공', color='green')
        self.ax.bar(x, maintain_rates, width, label='유지', color='yellow')
        self.ax.bar(x + width, destroy_rates, width, label='파괴', color='red')

        self.ax.set_xticks(x)
        self.ax.set_xticklabels([f'+{l}' for l in levels])
        self.ax.legend()
        self.canvas.draw()
```

#### Task 5.5: 실시간 업데이트 로직
- `src/gui/updater.py`: GUI 업데이트 스레드

```python
class GUIUpdater:
    def __init__(self, app: 'MacroApp', interval_ms: int = 500):
        self.app = app
        self.interval = interval_ms

    def start(self) -> None:
        """주기적 업데이트 시작"""
        self._update()

    def _update(self) -> None:
        """GUI 컴포넌트 업데이트"""
        # 상태 패널 업데이트
        self.app.status_panel.update(self.app.state)
        # 통계 패널 업데이트
        self.app.stats_panel.update(self.app.stats)
        # 차트 업데이트
        self.app.chart_panel.update(self.app.stats)
        # 다음 업데이트 예약
        self.app.root.after(self.interval, self._update)
```

#### Task 5.6: 설정 다이얼로그
- `src/gui/dialogs/settings_dialog.py`: 전략 파라미터 설정 창

```python
class SettingsDialog:
    """전략 설정 다이얼로그"""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("설정")

        # 레벨 임계값 설정
        ttk.Label(self.dialog, text="판매 레벨 임계값:").grid(row=0, column=0)
        self.level_threshold = ttk.Spinbox(self.dialog, from_=1, to=20)

        # 최대 실패 횟수 설정
        ttk.Label(self.dialog, text="최대 실패 횟수:").grid(row=1, column=0)
        self.max_fails = ttk.Spinbox(self.dialog, from_=1, to=10)

        # 저장/취소 버튼
        ttk.Button(self.dialog, text="저장", command=self.save).grid(row=2, column=0)
        ttk.Button(self.dialog, text="취소", command=self.dialog.destroy).grid(row=2, column=1)
```

### 4.6 Phase 6 상세 작업 (EXE 배포 및 문서화)

#### Task 6.1: PyInstaller 설정 및 빌드

##### 의존성 추가
```bash
uv add pyinstaller --dev
```

##### PyInstaller 스펙 파일 생성
- `build/sword-macro.spec`: 빌드 설정 파일

```python
# sword-macro.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/config/*.py', 'config'),
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='검키우기매크로',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='build/version_info.txt',
)
```

##### 버전 정보 파일
- `build/version_info.txt`: Windows 파일 속성에 표시될 버전 정보

```python
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041204B0',  # 한국어
        [
          StringStruct('CompanyName', '개인 프로젝트'),
          StringStruct('FileDescription', '검키우기 강화 매크로'),
          StringStruct('FileVersion', '1.0.0'),
          StringStruct('InternalName', 'sword-macro'),
          StringStruct('OriginalFilename', '검키우기매크로.exe'),
          StringStruct('ProductName', '검키우기 매크로'),
          StringStruct('ProductVersion', '1.0.0'),
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1042, 1200])])
  ]
)
```

##### 빌드 스크립트
- `scripts/build.bat`: Windows 빌드 스크립트

```batch
@echo off
echo [빌드 시작] 검키우기 매크로

REM 이전 빌드 정리
rmdir /s /q dist 2>nul
rmdir /s /q build\temp 2>nul

REM PyInstaller 실행
pyinstaller build/sword-macro.spec --distpath dist --workpath build/temp

echo.
if exist "dist\검키우기매크로.exe" (
    echo [성공] dist\검키우기매크로.exe 생성 완료
    echo 파일 크기:
    for %%A in ("dist\검키우기매크로.exe") do echo   %%~zA bytes
) else (
    echo [실패] EXE 파일 생성 실패
    exit /b 1
)
```

#### Task 6.2: 사용법 문서 작성

##### 문서 구조
```
docs/
├── README.md              # 메인 문서 (한글)
├── QUICK_START.md         # 빠른 시작 가이드
├── INSTALLATION.md        # 상세 설치 가이드
├── USAGE.md               # 상세 사용법
├── FAQ.md                 # 자주 묻는 질문
├── TROUBLESHOOTING.md     # 문제 해결 가이드
└── images/                # 스크린샷
    ├── setup_display.png
    ├── kakao_window.png
    ├── calibration.png
    └── dashboard.png
```

##### README.md 주요 내용
```markdown
# 검키우기 강화 매크로

카카오톡 검키우기 챗봇 게임의 강화를 자동화하는 프로그램입니다.

## 주요 기능
- 🗡️ 자동 강화 실행
- 📊 실시간 통계 및 차트
- ⚙️ 커스텀 전략 설정
- 💾 세션 기록 저장

## 빠른 시작

### 1. 다운로드
[최신 버전 다운로드](releases)에서 `검키우기매크로.exe` 다운로드

### 2. 사전 준비
- Windows 10/11
- 카카오톡 PC 설치
- 디스플레이 배율 100% 설정

### 3. 실행
1. `검키우기매크로.exe` 실행
2. 카카오톡에서 검키우기 채팅방 열기
3. "좌표 설정" 버튼으로 캘리브레이션
4. "시작" 버튼 클릭

## 단축키
| 키 | 기능 |
|----|------|
| F1 | 수동 강화 |
| F2 | 수동 판매 |
| F3 | 자동 모드 시작 |
| F4 | 일시정지 |
| F5 | 완전 정지 |
| ESC | 긴급 중단 |

## 주의사항
⚠️ 매크로 실행 중에는 해당 컴퓨터의 마우스/키보드 사용 불가
⚠️ 디스플레이 배율이 100%가 아니면 오작동 가능
⚠️ 카카오톡 창 위치 변경 시 재캘리브레이션 필요
```

##### QUICK_START.md 주요 내용
```markdown
# 빠른 시작 가이드 (5분 설정)

## Step 1: 디스플레이 설정 (1분)
1. 바탕화면 우클릭 > "디스플레이 설정"
2. "배율 및 레이아웃" 섹션에서 "100%" 선택
3. 로그아웃/로그인으로 적용

## Step 2: 카카오톡 준비 (1분)
1. 카카오톡 PC 실행
2. "검키우기" 검색 후 채팅방 열기
3. 창 크기와 위치 고정 (드래그하지 않기)

## Step 3: 매크로 실행 (1분)
1. `검키우기매크로.exe` 더블클릭
2. Windows Defender 경고 시 "추가 정보" > "실행" 클릭

## Step 4: 좌표 캘리브레이션 (2분)
1. "⚙️ 설정" 버튼 클릭
2. "좌표 설정" 탭 선택
3. "채팅 출력 영역" - 채팅 메시지가 보이는 곳 클릭
4. "채팅 입력 영역" - 메시지 입력창 클릭
5. "저장" 클릭

## Step 5: 매크로 시작
1. "▶️ 시작" 버튼 클릭 또는 F3 키
2. 자동 강화가 시작됩니다!

---

🎉 설정 완료! 매크로가 자동으로 강화를 진행합니다.
```

##### FAQ.md 주요 내용
```markdown
# 자주 묻는 질문 (FAQ)

## 설치 관련

### Q: EXE 파일이 바이러스로 감지됩니다
**A:** PyInstaller로 패키징된 프로그램은 종종 오탐지됩니다.
- Windows Defender: "추가 정보" > "실행" 클릭
- 또는 예외 폴더에 추가

### Q: 관리자 권한이 필요한가요?
**A:** 일반적으로 필요하지 않지만, 키보드/마우스 제어가 안 되면
우클릭 > "관리자 권한으로 실행"을 시도해보세요.

## 실행 관련

### Q: 클릭이 엉뚱한 곳에 됩니다
**A:** 디스플레이 배율 문제입니다.
설정 > 시스템 > 디스플레이 > 배율을 "100%"로 변경하세요.

### Q: 매크로 실행 중 다른 작업이 가능한가요?
**A:** 불가능합니다. 이 매크로는 실제 마우스/키보드를 제어합니다.
별도의 PC나 가상머신 사용을 권장합니다.

### Q: 한글 입력이 안 됩니다
**A:** 클립보드 방식을 사용하므로 한글 입력기 상태와 무관합니다.
다른 프로그램이 클립보드를 점유하고 있는지 확인하세요.

## 전략 관련

### Q: 최적의 판매 레벨은 몇인가요?
**A:** 일반적으로 10~12강 판매가 안정적입니다.
통계 탭에서 실제 수익률을 확인하며 조정하세요.

### Q: 파괴방지권은 언제 사용하나요?
**A:** 현재 버전에서는 수동 사용만 지원합니다.
자동 사용은 향후 업데이트 예정입니다.
```

##### TROUBLESHOOTING.md 주요 내용
```markdown
# 문제 해결 가이드

## 증상별 해결책

### 1. 프로그램이 실행되지 않음

#### 증상: 더블클릭해도 아무 반응 없음
**해결:**
1. Windows Defender 실시간 보호 일시 해제
2. 또는 예외 폴더에 추가
3. 관리자 권한으로 실행 시도

#### 증상: "VCRUNTIME140.dll을 찾을 수 없습니다"
**해결:**
Microsoft Visual C++ 재배포 가능 패키지 설치
https://aka.ms/vs/17/release/vc_redist.x64.exe

### 2. 좌표/클릭 문제

#### 증상: 클릭 위치가 어긋남
**해결:**
1. 디스플레이 배율 100% 확인
2. 좌표 재캘리브레이션
3. 카카오톡 창 위치가 변경되지 않았는지 확인

#### 증상: 전혀 클릭이 안 됨
**해결:**
1. 관리자 권한으로 실행
2. 다른 보안 프로그램(게임 가드 등) 비활성화

### 3. 파싱/인식 문제

#### 증상: 상태가 "UNKNOWN"으로 표시됨
**해결:**
1. 채팅 출력 영역 좌표 재설정
2. 채팅창에 새 메시지가 있는지 확인
3. 카카오톡 테마가 기본 테마인지 확인

### 4. 성능 문제

#### 증상: 반응이 느림
**해결:**
1. 설정에서 딜레이 값 감소 (최소 0.5초 권장)
2. 다른 프로그램 종료하여 시스템 부하 감소
3. 실시간 그래프 업데이트 주기 증가
```

#### Task 6.3: 릴리즈 패키지 구성

##### 릴리즈 폴더 구조
```
release/
├── 검키우기매크로_v1.0.0/
│   ├── 검키우기매크로.exe
│   ├── README.txt
│   ├── 빠른시작가이드.txt
│   └── config/
│       └── default_settings.json
└── 검키우기매크로_v1.0.0.zip
```

##### 릴리즈 스크립트
- `scripts/release.bat`: 릴리즈 패키지 생성

```batch
@echo off
setlocal enabledelayedexpansion

set VERSION=1.0.0
set RELEASE_NAME=검키우기매크로_v%VERSION%
set RELEASE_DIR=release\%RELEASE_NAME%

echo [릴리즈 생성] %RELEASE_NAME%

REM 기존 릴리즈 폴더 정리
rmdir /s /q "%RELEASE_DIR%" 2>nul
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\config"

REM 빌드 실행
call scripts\build.bat
if errorlevel 1 exit /b 1

REM 파일 복사
copy "dist\검키우기매크로.exe" "%RELEASE_DIR%\"
copy "docs\README.md" "%RELEASE_DIR%\README.txt"
copy "docs\QUICK_START.md" "%RELEASE_DIR%\빠른시작가이드.txt"
copy "src\config\default_settings.json" "%RELEASE_DIR%\config\"

REM ZIP 압축
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%' -DestinationPath 'release\%RELEASE_NAME%.zip' -Force"

echo.
echo [완료] 릴리즈 패키지 생성
echo   폴더: %RELEASE_DIR%
echo   압축: release\%RELEASE_NAME%.zip
```

---

## 5. 테스트 및 검증 방법

### 5.1 단위 테스트
- test_parser.py: 파서 테스트
- test_strategy.py: 전략 테스트
- test_env.py: RL 환경 테스트

### 5.2 통합 테스트
- 수동 체크리스트 기반 검증
- 1시간 연속 실행 안정성 테스트

### 5.3 성능 메트릭
| 메트릭 | 목표 |
|--------|------|
| 파싱 정확도 | >95% |
| 자동화 안정성 | >99% |
| AI 수익률 | >휴리스틱 |
| 응답 시간 | <500ms |

---

## 6. 위험 요소 및 대응

### 6.1 기술적 위험

| 위험 요소 | 심각도 | 대응 방안 |
|-----------|--------|-----------|
| Windows 권한 문제 | 높음 | 관리자 권한 실행 가이드 문서화 |
| 채팅 파싱 실패 | 높음 | 정규식 패턴 다양화 |
| 좌표 불일치 | 중간 | 캘리브레이션 도구 제공 |
| 입력 지연/누락 | 중간 | 딜레이 조정 |
| 디스플레이 배율 | 중간 | 100% 배율 설정 안내 |

### 6.2 Windows 10/11 설정

#### 필수 설정
```
1. Python 설치
   - python.org에서 Python 3.11+ 다운로드
   - 설치 시 "Add Python to PATH" 체크 필수

2. 관리자 권한 실행 (권장)
   - 일부 자동화 기능은 관리자 권한 필요
   - CMD/PowerShell을 "관리자 권한으로 실행"

3. 디스플레이 배율 설정
   - 설정 > 시스템 > 디스플레이 > 배율 100% 권장
   - 배율 변경 시 좌표 캘리브레이션 재실행 필요

4. 카카오톡 PC 설치
   - kakaotalk.com에서 Windows용 다운로드
   - 자동 업데이트 비활성화 권장
```

#### Windows Defender 예외 추가 (선택)
```
설정 > 개인 정보 및 보안 > Windows 보안 > 바이러스 및 위협 방지
> 설정 관리 > 제외 추가
> 매크로 폴더 경로 추가
```

### 6.3 서비스 정책 고려사항

**권장 사항:**
- 개인 사용 한정
- 적절한 딜레이 (최소 1초)
- 연속 사용 제한 (1시간마다 휴식)
- 로그 기록

### 6.4 멀티 모니터 & 백그라운드 실행 제한

#### Windows 멀티 모니터 좌표 체계

```
별도 Windows PC 모니터 구성 예시:

단일 모니터 (권장):
┌──────────────────────┐
│                      │
│    카카오톡 PC       │  ← 전체 화면 또는 고정 위치
│    + 매크로 실행      │
│                      │
│    (0,0) ~ (1920,1080)│
└──────────────────────┘

듀얼 모니터:
┌──────────────┬──────────────┐
│   모니터 1    │   모니터 2    │
│  (0,0)       │ (1920,0)     │
│   PRIMARY    │              │
│  카카오톡    │   (미사용)    │
└──────────────┴──────────────┘

- Win32 API는 화면 좌표를 클라이언트 좌표로 변환하여 사용
- 창 핸들(hwnd) 기반으로 카카오톡 창 자동 탐색
- RDP 환경에서도 PostMessage/SendMessage로 정상 동작
```

#### Windows 디스플레이 배율 주의사항

```
ℹ️ Win32 API 좌표 변환

Win32 API의 screen_to_client() 함수가 자동으로 좌표 변환 처리:
- 화면 좌표(screen coordinates)를 클라이언트 좌표(client coordinates)로 변환
- 창의 위치와 관계없이 올바른 좌표로 클릭
- 디스플레이 배율 영향 최소화

단, 캘리브레이션 시 좌표 설정은 화면 좌표 기준으로 진행
```

#### 백그라운드 실행: RDP 환경 지원

**Win32 API 사용으로 RDP 환경 지원:**

| 기능 | Win32 API 장점 |
|------|------|
| RDP 원격 접속 | PostMessage로 창에 직접 메시지 전송 |
| 창 핸들 기반 | 카카오톡 창을 자동으로 찾아서 제어 |
| 좌표 변환 | screen_to_client()로 정확한 좌표 계산 |
| 창 위치 무관 | hwnd 기반으로 창 위치 변경에 강함 |

#### 동시 작업을 위한 대안

| 방안 | 구현 난이도 | 장점 | 단점 |
|------|-------------|------|------|
| **1. 가상 머신 (VMware/Parallels)** | 중간 | 완전 분리, 안정적 | 메모리 2GB+ 필요, 카톡 재설치 |
| **2. 별도 PC/노트북** | 낮음 | 가장 확실 | 추가 하드웨어 비용 |
| **3. 전용 모니터 할당** | 낮음 | 간단함 | 해당 모니터 사용 불가 |
| **4. 원격 데스크톱** | 중간 | 네트워크로 분리 | 지연 발생 가능 |

#### 권장 운영 방식

```
┌─────────────────────────────────────────────────────────┐
│                    권장 운영 구성                         │
├──────────────┬───────────────────┬──────────────────────┤
│   모니터 1    │     모니터 2      │      모니터 3        │
│              │                   │                      │
│  사용자 작업  │  사용자 작업      │  카카오톡 + 매크로    │
│  (웹브라우저) │  (코딩/문서)      │  (전용 - 건드리지 X)  │
│              │                   │                      │
└──────────────┴───────────────────┴──────────────────────┘

주의: 모니터 3에서 매크로 실행 중에는 해당 화면을 터치하지 않아야 함
```

#### 향후 개선 가능성 (Phase 7 - 선택)

| 기능 | 설명 | 난이도 |
|------|------|--------|
| 창 핸들 기반 입력 | 특정 창에만 입력 전송 (Windows) | 높음 |
| 메모리 읽기 | 게임 상태를 메모리에서 직접 읽기 | 매우 높음 |
| 이미지 인식 기반 | 스크린샷으로 상태 파악 (OCR) | 중간 |

---

## 부록: 게임 데이터 테이블

```python
LEVEL_DATA = {
    0:  {"success": 0.995, "maintain": 0.005, "destroy": 0.000, "cost": 100,     "sell_price": 50},
    1:  {"success": 0.950, "maintain": 0.050, "destroy": 0.000, "cost": 200,     "sell_price": 150},
    2:  {"success": 0.900, "maintain": 0.100, "destroy": 0.000, "cost": 400,     "sell_price": 350},
    3:  {"success": 0.850, "maintain": 0.150, "destroy": 0.000, "cost": 800,     "sell_price": 700},
    4:  {"success": 0.800, "maintain": 0.200, "destroy": 0.000, "cost": 1500,    "sell_price": 1200},
    5:  {"success": 0.750, "maintain": 0.250, "destroy": 0.000, "cost": 3000,    "sell_price": 2500},
    6:  {"success": 0.700, "maintain": 0.300, "destroy": 0.000, "cost": 5000,    "sell_price": 4000},
    7:  {"success": 0.650, "maintain": 0.350, "destroy": 0.000, "cost": 10000,   "sell_price": 8000},
    8:  {"success": 0.600, "maintain": 0.400, "destroy": 0.000, "cost": 20000,   "sell_price": 15000},
    9:  {"success": 0.550, "maintain": 0.450, "destroy": 0.000, "cost": 40000,   "sell_price": 30000},
    10: {"success": 0.500, "maintain": 0.450, "destroy": 0.050, "cost": 80000,   "sell_price": 60000},
    11: {"success": 0.450, "maintain": 0.400, "destroy": 0.150, "cost": 150000,  "sell_price": 120000},
    12: {"success": 0.400, "maintain": 0.350, "destroy": 0.250, "cost": 300000,  "sell_price": 250000},
    13: {"success": 0.300, "maintain": 0.300, "destroy": 0.400, "cost": 500000,  "sell_price": 500000},
    14: {"success": 0.200, "maintain": 0.300, "destroy": 0.500, "cost": 1000000, "sell_price": 1000000},
    15: {"success": 0.150, "maintain": 0.250, "destroy": 0.600, "cost": 2000000, "sell_price": 3000000},
    16: {"success": 0.100, "maintain": 0.200, "destroy": 0.700, "cost": 3000000, "sell_price": 5000000},
    17: {"success": 0.080, "maintain": 0.170, "destroy": 0.750, "cost": 5000000, "sell_price": 10000000},
    18: {"success": 0.060, "maintain": 0.140, "destroy": 0.800, "cost": 7000000, "sell_price": 20000000},
    19: {"success": 0.050, "maintain": 0.100, "destroy": 0.850, "cost": 10000000,"sell_price": 50000000},
    20: {"success": 0.000, "maintain": 0.000, "destroy": 0.000, "cost": 0,       "sell_price": 100000000},
}
```

---

## 참고 레포지토리

- [minsoo0926/sword-macro](https://github.com/minsoo0926/sword-macro) - 카카오톡 검키우기 게임 강화학습 및 매크로
