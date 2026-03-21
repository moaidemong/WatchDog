# 06. Evaluation and Iteration

## 1. 평가 목적
이 프로젝트의 평가는 "벤치마크 점수"보다 "실제 알림 품질"이 더 중요하다.

따라서 offline metric과 online metric을 분리해서 본다.

## 2. 오프라인 평가
### 2.1 기본 분류 지표
- precision
- recall
- F1 score
- confusion matrix

특히 중요한 클래스:
- `get_up_fail`
- `collapse_or_fall`

### 2.2 이벤트 단위 평가
프레임이 아니라 이벤트 기준으로 평가한다.
- true positive event
- false positive event
- false negative event

### 2.3 시간 지표
안전 알림이므로 아래 지표도 중요하다.
- detection latency
- alert latency
- time-to-notification
- recovery detection lag

## 3. 온라인 평가
### 핵심 운영 지표
- 하루 오탐 수
- 주간 미탐 추정 수
- 실제 유용한 알림 비율
- 사용자가 무시한 알림 비율
- 재알림 과다 여부

## 4. 경보 품질의 실제 기준
이 시스템은 아래 상태가 되어야 쓸 만하다.

- 중요한 실패 사건을 종종 놓치더라도 완전히 무용하지 않음
- 알림이 너무 많아져 꺼버리는 수준은 피함
- 시간이 지날수록 오탐/미탐이 줄어듦

## 5. 실험 순서
### Experiment 1
rules only
- body height threshold
- attempt count threshold
- timeout tuning

### Experiment 2
rules + feature classifier
- RandomForest / XGBoost

### Experiment 3
rules + classifier ensemble
- weighted score
- alert threshold optimization

### Experiment 4
camera and ROI tuning
- 모델보다 카메라 위치가 더 크게 영향 줄 수 있음

## 6. 검증 셋 관리
중요:
- 같은 이벤트의 파생 프레임이 train/val/test에 중복되면 안 된다.
- 가능한 한 날짜 분리 또는 사건 분리
- 실운영 데이터 일부는 마지막까지 hold-out

## 7. 오류 분석 템플릿
각 오탐/미탐은 아래 항목으로 분석한다.
- event_id
- predicted label
- true label
- camera
- day/night
- pose quality
- occlusion level
- root cause
- fix idea

예:
```text
cause: blanket occlusion caused low hip confidence
fix: add occluded samples, lower dependency on hind paw features
```

## 8. 액티브 러닝 루프
1. 운영 중 이벤트 수집
2. 오탐/미탐 우선 검토
3. 어려운 샘플에 정답 라벨 부여
4. pose/feature/classifier 재학습
5. 새 버전 shadow evaluation
6. 성능 개선 시 승격

## 9. 버전 관리
아래는 버전으로 관리한다.
- pose model version
- classifier version
- threshold version
- label schema version
- dataset snapshot version

## 10. 추천 보고서 템플릿
각 버전마다 아래를 남긴다.
- 변경점
- 데이터셋 요약
- train/val/test 결과
- false positive 사례 5건
- false negative 사례 5건
- threshold 변화
- 운영 결과
- rollout 여부

## 11. 성공적인 개선의 정의
- false negative 감소 또는
- false positive 감소 또는
- alert latency 개선 또는
- 운영 안정성 개선

단일 점수만으로 승격하지 않는다.
