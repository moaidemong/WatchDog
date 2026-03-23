# DECISION-0001: Raspberry Pi 5 + AI HAT+ Topology

## 상태
Accepted

## 배경
현재 운영 환경은 다음과 같다.

- Raspberry Pi 5 8GB
- AI HAT+ 26 TOPS
- Camera Module v3
- 단일 카메라 기준 1차 MVP

기존 문서는 전체 파이프라인 방향은 잘 정의하고 있지만, 어떤 레이어를 CPU에서 돌리고 어떤 레이어를 가속기에 올릴지에 대한 현장 의사결정이 빠져 있었다.

## 결정
1차 운영 토폴로지는 아래처럼 고정한다.

```text
[Camera Module v3]
        |
        v
[Frame Ingest / Timestamp / Ring Buffer]      <- Raspberry Pi CPU
        |
        v
[Motion Gate / ROI Crop]                      <- Raspberry Pi CPU
        |
        v
[Dog Detection]                               <- AI HAT+ 우선
        |
        v
[Event Clip Save / Metadata]                  <- Raspberry Pi CPU + local storage
        |
        v
[Pose Estimation on Event Frames]             <- 초기 CPU 또는 경량 가속
        |
        v
[Feature Extraction / Rule Engine]            <- Raspberry Pi CPU
        |
        +---------------------------+
        |                           |
        v                           v
[Notifier]                    [Review Queue / Labels]
```

## 이유
- 항상 전체 프레임에 대해 무거운 추론을 돌리지 않고, detection 결과를 이벤트 게이트로 사용하면 엣지 장비에서 지속 운영이 쉽다.
- AI HAT+는 가장 호출 빈도가 높은 detection 레이어에 먼저 투입하는 것이 효과가 크다.
- pose는 초기에는 이벤트 클립에 대해서만 제한적으로 수행해도 충분하므로, MVP 단계에서는 CPU fallback이 가능하다.
- feature extraction, rules, alert deduplication은 계산량이 작고 explainability가 중요하므로 CPU가 적합하다.

## 운영 원칙
- detection은 실시간에 가깝게 유지한다.
- pose는 후보 이벤트에만 수행한다.
- 분류는 frame 단위가 아니라 event 단위로 기록한다.
- 저장되는 모든 알림에는 explainable metadata를 남긴다.

## 1차 구성
- ingest: Camera Module v3 직접 입력
- detection: AI HAT+ 호환 dog detector
- event extraction: Python 서비스
- pose inference: 이벤트 재생 기반 비동기 작업
- decision: rules first
- notification: Telegram 우선
- storage: 로컬 파일 + 필요 시 SQLite

## 대안과 기각 이유
### 대안 A. 모든 추론을 CPU에서 처리
기각 이유:
- 장시간 운영 시 여유가 부족할 수 있다.
- detection을 지속 수행하는 비용이 가장 크다.

### 대안 B. detection과 pose를 모두 항상 가속기에서 처리
기각 이유:
- 초기 모델/런타임 통합 복잡도가 높다.
- 데이터와 threshold가 고정되기 전에 시스템 복잡도가 과도하게 올라간다.

### 대안 C. 처음부터 Frigate 분리 구조로 진행
기각 이유:
- MVP 속도보다 운영 구성 복잡도가 먼저 증가한다.
- 단일 카메라 기준에서는 순수 Python 토폴로지가 더 빠르다.

## 후속 작업
- AI HAT+에서 사용할 detector 런타임과 모델 포맷 결정
- pose 단계의 CPU latency 측정
- 필요 시 Phase 2 이후 Frigate + custom inference 분리 검토
