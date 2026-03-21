# 03. Modeling Strategy

## 1. 기본 입장
이 프로젝트는 **적은 샘플로 가능한 구조**를 택한다.

따라서 1차 접근은 아래 순서다.

1. 개 탐지
2. 포즈 추정
3. 시계열 특징 추출
4. 규칙 기반 판정
5. 경량 분류기 보강

## 2. 왜 end-to-end video classifier를 1차로 권장하지 않는가
- 기상 실패는 희귀 이벤트다.
- raw video로 바로 학습하려면 데이터가 많이 필요하다.
- 야간/가림/카메라 각도 편차에 취약하다.
- 왜 알림이 났는지 설명하기 어렵다.

반면 포즈 기반 방식은:
- 적은 샘플에 유리
- 해석 가능
- 규칙 엔진과 혼합 가능
- 실패 원인 분석이 쉬움

## 3. 추천 모델 계층
### 3.1 Detection Layer
입력:
- frame

출력:
- dog bounding box
- confidence

후보:
- Frigate 내 detection
- YOLOv8/v11 small model
- TensorRT/ONNX 최적화 가능

### 3.2 Pose Layer
입력:
- dog crop

출력:
- keypoints + confidence

후보:
- DeepLabCut
- SLEAP
- YOLO Pose fine-tuned on dog data

### 3.3 Temporal Feature Layer
입력:
- keypoint time series

출력:
- event features vector

추천 특징:
- body center height statistics
- neck-to-hip line angle
- paw displacement
- number of lift attempts
- time to stable stand
- lateral sway
- stillness after attempts
- duration in low posture
- pose confidence stability

### 3.4 Decision Layer
출력:
- rest_normal
- get_up_success
- get_up_fail
- collapse_or_fall
- ambiguous

추천 순서:
- Rule engine
- RandomForest / XGBoost
- small temporal model if needed

## 4. 1차 규칙 기반 판정 예시
```text
if
  low_posture_duration >= T1
  and attempt_count >= N
  and standing_state_not_reached_within <= T2
  and motion_instability >= M
then
  predict failed_get_up
```

이 규칙은 초기 positive 생성기 역할도 할 수 있다.

## 5. 상태 기계(State Machine) 설계
행동 인식을 더 안정적으로 하려면 상태 기계를 사용한다.

### 상태 예시
- `unknown`
- `resting`
- `attempting_to_rise`
- `standing`
- `failed_to_rise`
- `collapsed`
- `human_assist`

### 전이 예시
```text
resting -> attempting_to_rise
attempting_to_rise -> standing
attempting_to_rise -> failed_to_rise
standing -> collapsed
failed_to_rise -> human_assist
```

장점:
- 단일 프레임 오판을 완화
- 시간축 의미를 반영
- 알림 로직 설명 가능

## 6. 추천 학습 전략
### 6.1 Stage 1
- 포즈 모델은 공개 모델 또는 적은 라벨 파인튜닝
- 행동 판정은 rules only

### 6.2 Stage 2
- event-level feature dataset 구축
- RandomForest 또는 XGBoost 학습
- feature importance 확인

### 6.3 Stage 3
필요 시:
- 1D temporal CNN
- TCN
- small LSTM/GRU

단, Stage 3는 Stage 2가 충분히 성숙한 뒤 진행

## 7. 추천 feature 목록
### 자세 기하학
- nose_y, neck_y, hip_y normalized
- torso angle
- front leg extension
- hind leg fold angle

### 움직임
- velocity of keypoints
- acceleration peaks
- jerk or irregular motion score

### 시도 관련
- rise attempt count
- attempt duration
- max torso lift without stand
- recovery failure duration

### 안정성
- sway amplitude
- repeated micro-adjustment score
- pose confidence dropout ratio

## 8. positive 정의를 기계적으로 만드는 방법
`failed_get_up`는 감정어가 아니라 규칙으로 정의한다.

예시:
- resting 상태에서 시작
- 2초 이상 몸통/목/엉덩이의 상승 시도가 존재
- 10초 이내 standing threshold 미달
- 2회 이상 재시도
- 이후 다시 low posture로 회귀

이 정의는 라벨링과 모델 목표를 일치시킨다.

## 9. 모델 산출물
- `dog_detector.onnx`
- `dog_pose_model.pt`
- `event_feature_schema.json`
- `failed_rise_classifier.pkl`
- `thresholds.yaml`

## 10. 해석 가능성
안전 알림 시스템이므로 아래를 남긴다.
- 최종 점수
- 기여한 룰/특징
- standing 미도달 시간
- 시도 횟수
- 대표 스냅샷
- 포즈 오버레이 클립

## 11. 확장 방향
후속 단계에서 가능:
- 다수 개체 추적
- 바닥 영역 위험도 맵
- 품종/체형별 threshold 분리
- IMU 센서 결합
- 음성/울음 소리와 멀티모달 결합
