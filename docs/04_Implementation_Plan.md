# 04. Implementation Plan

## 1. 구현 전략
큰 시스템을 한 번에 만들지 않는다.
작게 시작해서 실제 영상을 기반으로 반복 개선한다.

## 2. 단계별 로드맵

### Phase 0. 준비
목표:
- 카메라 환경 고정
- 저장소 구조 생성
- 문서/라벨 기준 정리

산출물:
- repo 초기화
- `.env.example`
- 카메라 목록
- 디렉터리 구조
- 샘플 영상 몇 개

### Phase 1. 이벤트 수집 MVP
목표:
- 개가 화면에 있을 때 클립 저장
- 수동 검토 가능한 이벤트 큐 생성

기능:
- RTSP ingest
- dog detection
- motion gate
- event clip save
- metadata save

완료 기준:
- 하루 운영 후 이벤트 클립이 자동 저장됨

### Phase 2. 라벨링 워크플로
목표:
- 이벤트에 라벨 부여
- 대표 프레임 포즈 라벨링

기능:
- review CSV
- 간단한 clip review UI 또는 notebook workflow
- pose label export

완료 기준:
- `get_up_success`, `get_up_fail`, `rest_normal` 최소 수십 건 확보

### Phase 3. 포즈 추정 구축
목표:
- 대표 프레임에서 안정적으로 keypoint 추정

기능:
- pose dataset 구성
- 초기 fine-tuning
- inference script
- keypoint JSON 저장

완료 기준:
- 주/야간 주요 자세에서 keypoint가 usable quality 확보

### Phase 4. 규칙 기반 실패 판정
목표:
- 1차 실용 알람 동작

기능:
- low posture 판정
- attempt count 추정
- standing 전이 판정
- failed_get_up rule scoring
- 메신저 알림

완료 기준:
- 실제 실패 장면에서 알림이 발생
- 오탐 수준이 운영 가능 범위

### Phase 5. 특징 기반 분류기 추가
목표:
- 규칙 기반 성능 보강

기능:
- event feature extractor
- train/val/test split
- RandomForest/XGBoost 학습
- threshold tuning

완료 기준:
- 규칙 only 대비 precision/recall 개선

### Phase 6. 운영 안정화
목표:
- 장시간 자동 운영
- 모델 버전 관리
- 재학습 루프 마련

기능:
- retraining scripts
- model registry
- alert deduplication
- health checks
- review dashboard

완료 기준:
- 지속 운용 가능
- 오탐/미탐 사례가 개선 루프로 연결됨

## 3. 권장 리포지토리 구조
```text
dog-rise-alert/
  README.md
  AGENTS.md
  .env.example
  pyproject.toml
  requirements.txt
  configs/
    cameras.yaml
    thresholds.yaml
    labels.yaml
  app/
    ingest/
    detection/
    events/
    pose/
    features/
    rules/
    classifier/
    notify/
    storage/
    api/
  scripts/
    run_ingest.py
    extract_events.py
    label_export.py
    train_pose.py
    train_classifier.py
    run_inference.py
  data/
    raw/
    events/
    labels/
    models/
  notebooks/
  tests/
  docs/
```

## 4. 스프린트 제안
### Sprint 1
- RTSP ingest
- dog detection
- event save
- logs

### Sprint 2
- review tooling
- labeling schema
- event metadata cleanup

### Sprint 3
- pose inference pipeline
- visualization script

### Sprint 4
- rule engine
- Telegram/Slack notifier

### Sprint 5
- feature extraction
- baseline classifier
- evaluation report

## 5. MVP 기술 우선순위
### 반드시 필요한 것
- event capture
- labeling
- pose inference
- rule engine
- notification

### 나중에 해도 되는 것
- fancy dashboard
- web admin
- multi-camera orchestration
- active learning automation
- edge acceleration tuning

## 6. 추천 구현 순서 상세
1. RTSP에서 1fps 또는 2fps로 샘플링
2. 개 탐지해서 존재 시 short clip 저장
3. 수동으로 실패/성공/휴식 라벨링
4. 대표 프레임 포즈 라벨링
5. 포즈 모델 적용
6. 키포인트 기반 body height/attempt features 계산
7. rule engine 작성
8. 알림 연결
9. 실운영
10. 오탐/미탐 기반 classifier 보강

## 7. 초기 threshold 예시
```yaml
low_posture_min_seconds: 4
attempt_window_seconds: 10
min_attempt_count: 2
standing_recovery_timeout_seconds: 10
alert_cooldown_seconds: 180
min_pose_confidence: 0.55
```

## 8. 도구 선택 가이드
### Frigate 사용 시
적합:
- 기존 NVR/RTSP 운영 경험 있음
- MQTT event 기반 확장 원함

### 순수 Python로 시작 시
적합:
- 빠른 실험 우선
- 의존성 최소화
- 단일 카메라 MVP

추천:
- MVP는 순수 Python
- 실운영은 Frigate + custom inference 분리 검토

## 9. 1차 완료 정의
다음이 모두 되면 1차 완료로 본다.
- 카메라 1대에서 자동 수집
- 실패 장면 최소 수십 건 확보
- 포즈 기반 rule alert 동작
- 메신저 알림 전송
- 이벤트 검토 및 재학습 재료 축적
