# 01. System Architecture

## 1. 개요
시스템은 아래 다섯 층으로 나뉜다.

1. 영상 입력층
2. 이벤트 추출층
3. 자세/행동 판정층
4. 알림/저장층
5. 운영/재학습층

## 2. 전체 아키텍처

```text
[CCTV / RTSP / NVR]
        |
        v
[Frame Ingest / Stream Reader]
        |
        v
[Dog Detection / Motion Gate]
        |
        v
[Event Clip Extractor]
        |
        v
[Pose Estimation]
        |
        v
[Temporal Feature Builder]
        |
        v
[Rule Engine + Small Classifier]
        |
        +----------------------+
        |                      |
        v                      v
[Notification Service]   [Event Storage / Review Queue]
                               |
                               v
                        [Label Review / Retraining]
```

## 3. 모듈 설명

### 3.1 Frame Ingest
책임:
- RTSP 또는 파일 입력 수신
- 프레임 디코딩
- FPS 다운샘플링
- 타임스탬프 부여

입력:
- RTSP URL 또는 video file

출력:
- 표준화된 frame stream

### 3.2 Dog Detection / Motion Gate
책임:
- 프레임 내 반려견 존재 여부 판단
- 필요 시 관심 영역(ROI) 추출
- 움직임이 거의 없는 구간은 계산 절약

선택지:
- Frigate의 object detection 사용
- YOLO 계열 모델 직접 사용
- 배경 차분 + object detection 병행

### 3.3 Event Clip Extractor
책임:
- 이벤트 후보 구간 전후 buffer 포함 저장
- 예: 전 10초 + 후 20초
- 추론용 clip / 리뷰용 clip 생성

이 단계의 목표:
- 전체 스트림을 계속 정밀 분석하지 않고 **후보 이벤트만** 후속 분석

### 3.4 Pose Estimation
책임:
- 개의 keypoints 추정
- 프레임별 자세 좌표 생성

후보 도구:
- DeepLabCut
- SLEAP
- YOLO Pose 파인튜닝
- MediaPipe는 인체 중심이라 우선순위 낮음

출력 예:
```json
{
  "frame_id": 1234,
  "dog_id": 1,
  "keypoints": {
    "nose": [100, 210, 0.92],
    "neck": [130, 240, 0.88],
    "spine": [190, 260, 0.84],
    "front_left_paw": [120, 320, 0.71]
  }
}
```

### 3.5 Temporal Feature Builder
책임:
- 프레임별 포즈를 이벤트 단위 특징으로 변환
- 예:
  - 몸통 높이 변화량
  - 머리/어깨/골반의 상대 고도
  - 발 위치 이동량
  - 자세 각도 변화
  - lifting attempt 횟수
  - standing 전이 여부
  - 자세 불안정성 지표
  - 움직임 주기성

### 3.6 Rule Engine + Small Classifier
책임:
- 1차 룰 기반 필터
- 2차 분류기 점수 결합
- 최종 alarm score 계산

추천 구조:
- 초기: pure rule engine
- 이후: RandomForest / XGBoost / LightGBM / small MLP / temporal CNN 추가

### 3.7 Notification Service
책임:
- 메신저 전송
- rate limiting
- 중복 이벤트 억제
- 이벤트 링크/클립/스냅샷 첨부

### 3.8 Event Storage / Review Queue
책임:
- 이벤트 원본/요약/메타데이터 저장
- 사람 검토용 큐 제공
- 정답 라벨 저장
- 학습 데이터로 재사용

## 4. 권장 배포 토폴로지

### 옵션 A. 단일 머신
- RTSP ingest
- detection
- pose
- classifier
- notifier
- database
- review UI

장점:
- 단순
- 1인 운영 적합

단점:
- 카메라 수 확장성 낮음

### 옵션 B. Frigate + Custom Inference 분리
```text
[Frigate]
  - camera ingest
  - object detection
  - snapshots/clips
  - MQTT events

[Custom Service]
  - pose estimation
  - behavior scoring
  - alerting
  - review queue
```

장점:
- 역할 분리 명확
- NVR 기능 재사용
- 운영 편리

권장:
- 1차 실전 운영은 이 구성이 현실적

## 5. 데이터 저장 구조
### 테이블 예시
- cameras
- events
- event_frames
- event_pose
- event_features
- event_labels
- notifications
- model_versions

### 이벤트 레코드 예시
```json
{
  "event_id": "evt_20260320_001",
  "camera_id": "livingroom_01",
  "start_ts": "2026-03-20T10:10:00Z",
  "end_ts": "2026-03-20T10:10:18Z",
  "status": "alerted",
  "predicted_label": "failed_get_up",
  "score": 0.91,
  "clip_path": "/data/events/evt_20260320_001.mp4",
  "snapshot_path": "/data/events/evt_20260320_001.jpg"
}
```

## 6. MVP 아키텍처 권장안
초기에는 아래 순서가 가장 좋다.

1. Frigate 또는 YOLO로 dog detection
2. 이벤트 클립 저장
3. 수동 리뷰
4. DeepLabCut/SLEAP로 pose pipeline 구축
5. 규칙 기반 failed_get_up 판정
6. 알림 연결
7. 로그/평가/반복

## 7. 왜 이 구조가 적은 샘플에 유리한가
- raw video 전체를 직접 학습하지 않음
- 이미 학습된 dog detection / pose 추정 모델을 재사용
- 사용자 데이터는 마지막 행동 판정 단계에 집중
- 기상 실패라는 희귀 이벤트를 **상태 전이 문제**로 재정의
