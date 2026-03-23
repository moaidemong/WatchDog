# Dog Rise Alert

노견이 **일어나고 싶어도 제대로 일어나지 못하는 상황**을 CCTV 기반으로 감지하고, 메신저로 빠르게 알림을 보내는 프로젝트 문서 세트입니다.

## 문서 구성
- `00_Project_Charter.md` — 프로젝트 목표, 범위, 성공 기준
- `01_System_Architecture.md` — 전체 시스템 구조
- `02_Data_Collection_and_Labeling.md` — 데이터 수집, 이벤트 추출, 라벨링 규칙
- `03_Modeling_Strategy.md` — 포즈 추정 + 상태 전이 기반 모델링 전략
- `04_Implementation_Plan.md` — 단계별 구현 계획
- `05_Notification_and_Deployment.md` — 알림, 배포, 운영
- `06_Evaluation_and_Iteration.md` — 평가 기준, 실험, 액티브 러닝
- `07_VSCode_ChatGPT_5_4_Working_Guide.md` — VSCode에서 ChatGPT 5.4와 협업하는 방식
- `08_Risk_and_Safety.md` — 한계, 오탐/미탐, 안전 대책
- `decisions/DECISION-0001-raspberry-pi-ai-hat-topology.md` — 라즈베리파이 5 + AI HAT+ 실행 토폴로지 결정
- `decisions/DECISION-0002-camera-placement-and-roi.md` — Camera Module v3 설치/ROI 운영 기준
- `decisions/DECISION-0003-edge-inference-budget.md` — 엣지 추론 자원 예산과 운영 임계치
- `AGENTS.md` — AI 협업 에이전트용 운영 지침

## 핵심 아이디어
이 프로젝트는 처음부터 "raw video → end-to-end 행동 분류"로 가지 않습니다.

대신 아래처럼 쪼갭니다.

1. CCTV에서 **반려견 존재/이벤트 구간**을 잡는다.
2. 이벤트 구간에서 **자세/포즈**를 추정한다.
3. 시간축 특징과 상태 전이를 이용해 **기상 성공 / 기상 실패 / 단순 휴식**을 구분한다.
4. 조건이 맞으면 **메신저 알림**을 보낸다.

즉, 적은 샘플로도 가능한 구조를 선택합니다.

## 권장 1차 기술 스택
- Python 3.11+
- OpenCV
- YOLO 계열 또는 Frigate 기반 개 탐지
- DeepLabCut 또는 SLEAP 또는 YOLO Pose 기반 개 포즈 추정
- scikit-learn 또는 경량 PyTorch 분류기
- FastAPI
- MQTT / Telegram / Kakao Work / Slack / Discord 중 하나
- Docker / Docker Compose
- SQLite 또는 PostgreSQL

## 1차 목표
**노견이 일어나고 싶어도 일정 시간 이상 일어나지 못하는 상황을 놓치지 않는 것**이 목표입니다.

이 프로젝트의 1차 성공은 "완벽한 행동 인식"이 아니라 아래 조건을 만족하는 것입니다.

- 야간/주간 모두 동작
- 반려견이 자주 머무는 구역에서 안정적으로 이벤트 감지
- 기상 실패 이벤트에 대해 실용적인 수준의 알림 정확도 확보
- 오탐이 너무 많지 않아 실제로 계속 켜 둘 수 있음

## 빠른 시작 순서
1. `00_Project_Charter.md` 읽기
2. `01_System_Architecture.md` 읽기
3. `02_Data_Collection_and_Labeling.md` 기반으로 데이터 수집 시작
4. `04_Implementation_Plan.md` 순서대로 MVP 구현
5. `06_Evaluation_and_Iteration.md`로 반복 개선
6. `decisions/` 문서로 실제 장비 토폴로지와 운영 예산 고정

## 구현 철학
- 작은 문제로 쪼개기
- 적은 샘플로 가능한 구조 선택
- 규칙 기반 + 모델 기반을 혼합
- 안전 알림 목적이므로 해석 가능한 파이프라인 유지
- 처음부터 대형 GPU/대형 모델을 전제하지 않음
