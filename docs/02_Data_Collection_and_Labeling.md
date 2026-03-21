# 02. Data Collection and Labeling

## 1. 목표
기상 실패 알림 시스템을 만들기 위해 필요한 데이터 수집 및 라벨링 전략을 정의한다.

핵심은 "영상 전체를 무작정 모으는 것"이 아니라 **의미 있는 이벤트 구간을 체계적으로 축적하는 것**이다.

## 2. 수집 원칙
### 2.1 환경 고정
가능한 한 아래 조건을 고정한다.
- 카메라 위치
- 카메라 화각
- 주요 휴식 구역
- 해상도/FPS
- 야간 IR 설정

고정된 환경은 적은 샘플에서도 일반화 성능을 높인다.

### 2.2 이벤트 중심 수집
전체 24시간 영상을 모두 라벨링하지 않는다.
다음 이벤트만 추출한다.
- 눕기
- 일어나기
- 일어나려다 실패하기
- 쓰러짐/비정상 자세 진입
- 장시간 누워 있음
- 사람 개입 후 회복

### 2.3 전후 문맥 포함
이벤트는 전후 buffer를 포함해서 저장한다.
권장:
- pre-roll: 10초
- post-roll: 20초
- 길이: 20~45초

## 3. 우선 수집해야 할 클래스
1차 분류를 위한 추천 클래스:

- `rest_normal`
  - 편하게 누워 있거나 쉬는 상태
- `get_up_success`
  - 누운 상태에서 정상적으로 일어남
- `get_up_fail`
  - 일어나려는 시도는 있으나 standing으로 전이 실패
- `collapse_or_fall`
  - 갑작스러운 쓰러짐 또는 비정상 자세 진입
- `ambiguous`
  - 판정 애매함
- `human_assist`
  - 사람이 와서 도와준 경우

## 4. 라벨 수준
데이터는 3단계로 라벨링한다.

### 4.1 Clip-level label
클립 전체에 대해 대표 라벨 부여
예:
- get_up_fail
- get_up_success

### 4.2 Phase annotation
이벤트 내부 구간을 단계별로 표시
예:
- resting
- attempt_start
- repeated_attempt
- stand_success
- stand_fail
- human_intervention

### 4.3 Frame / key event annotation
필요 시 핵심 시점 표시
예:
- 첫 시도 시작 프레임
- 몸통 최대 상승 프레임
- standing 전환 프레임
- 포기 시점

## 5. 포즈 라벨링 전략
포즈 모델은 모든 프레임을 라벨링할 필요가 없다.
대표 프레임을 샘플링한다.

### 5.1 추천 샘플링 기준
- 낮/밤
- 좌/우 방향
- 엎드림/옆으로 누움/반쯤 일어남
- 장애물/이불/쿠션 존재
- 가까움/멀음
- 정상 기상 / 실패 기상

### 5.2 포즈 라벨 후보 keypoints
프로젝트 단순화를 위해 1차는 적은 keypoint로 간다.
추천:
- nose
- neck
- shoulder center
- spine center
- hip center
- front_left_paw
- front_right_paw
- hind_left_paw
- hind_right_paw
- tail_base

### 5.3 라벨링 최소 세트
- 초기: 80~150 대표 프레임
- 1차 보강: 오탐/미탐 기반 50~100 프레임 추가
- 반복: 실패 사례 위주로 보강

## 6. 라벨 정의 예시
### get_up_success
누운 상태에서 1회 또는 소수의 시도 후 정상 standing 상태로 전이

### get_up_fail
다음 조건을 모두 만족하는 경우 우선 positive 후보로 본다.
- resting 또는 low posture 상태에서 시작
- 최소 1회 이상 몸통 상승 시도
- 지정 시간 안에 standing 도달 실패
- 시도 반복 또는 불안정한 움직임 존재

### collapse_or_fall
다음 중 하나:
- standing 또는 semi-standing에서 급격히 낮은 자세로 전이
- 비정상적 측면 전도
- 갑작스러운 균형 상실

### ambiguous
아래 중 하나:
- 화면 가림이 심함
- 사람/물체가 개를 가림
- 체위 구분이 불명확
- sleeping twitch와 실패 시도가 구분되지 않음

## 7. 데이터셋 디렉터리 구조 예시
```text
data/
  raw/
    camera_livingroom_01/
      2026-03-20/
  events/
    evt_000001/
      clip.mp4
      snapshot.jpg
      meta.json
    evt_000002/
  labels/
    clips.csv
    phases.csv
    pose_frames/
      evt_000001_0012.jpg
      evt_000001_0048.jpg
    pose_annotations.json
  splits/
    train_events.txt
    val_events.txt
    test_events.txt
```

## 8. CSV 예시
### clips.csv
```csv
event_id,camera_id,start_ts,end_ts,label,review_status,notes
evt_000001,living01,2026-03-20T10:10:00,2026-03-20T10:10:18,get_up_fail,approved,front paws slipped
evt_000002,living01,2026-03-20T11:05:03,2026-03-20T11:05:12,get_up_success,approved,rose in one try
```

### phases.csv
```csv
event_id,phase,start_frame,end_frame
evt_000001,resting,0,52
evt_000001,attempt_start,53,75
evt_000001,repeated_attempt,76,161
evt_000001,stand_fail,162,200
```

## 9. 데이터 분할 원칙
중요:
- 같은 이벤트에서 뽑은 프레임이 train/test에 섞이면 안 된다.
- 분할은 **frame 기준이 아니라 event 기준**으로 한다.
- 가능하면 날짜/상황 기준 분리도 고려한다.

권장:
- train: 70%
- val: 15%
- test: 15%

## 10. 액티브 러닝 전략
초기에는 완벽한 데이터셋을 만들려 하지 않는다.

반복 루프:
1. 초안 모델/룰로 운영
2. 오탐/미탐 이벤트 저장
3. 검토 후 정답 라벨 부여
4. 어려운 샘플 우선 보강
5. 재학습

## 11. 금지할 실수
- 프레임 단위 랜덤 분할
- positive 정의가 모호한 상태로 라벨링
- 너무 다양한 카메라 환경을 한 번에 섞기
- 애매한 샘플을 억지로 positive/negative로 분류
- 사람이 리뷰하지 않은 자동 라벨을 바로 정답셋으로 쓰기
