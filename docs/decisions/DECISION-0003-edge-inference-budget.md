# DECISION-0003: Edge Inference Budget

## 상태
Accepted

## 배경
Raspberry Pi 5 8GB는 단일 카메라 MVP에는 충분하지만, 장시간 운영에서는 FPS, 온도, 저장 용량, 알림 지연을 명시적으로 관리해야 한다. 문서에는 단계별 아키텍처는 있으나, 실제 엣지 장비에서의 자원 예산은 정리되어 있지 않았다.

## 결정
1차 운영에서는 아래 예산을 기준으로 시스템을 조정한다.

## 처리 예산
- ingest sampling: 1 FPS에서 시작, 필요 시 2 FPS까지 허용
- detection target latency: frame당 300 ms 이하 목표
- pose inference: 이벤트 클립에 대해서만 수행
- alert latency target: 이벤트 조건 만족 후 15초 이내
- cooldown: 동일 이벤트 유형 기준 180초 이상

## 저장 예산
- 원본 24시간 상시 저장을 기본 전제로 두지 않는다.
- 이벤트 클립 중심 저장을 기본 정책으로 한다.
- 기본 이벤트 보존 기간과 최대 디스크 사용량을 설정 파일로 분리한다.
- 저장 용량 80% 도달 시 오래된 low-priority artifact부터 정리한다.

## 안정성 예산
- 장비 온도, 마지막 프레임 수신 시각, notifier 실패 횟수를 헬스체크에 포함한다.
- 연속 카메라 입력 실패가 일정 횟수 이상이면 degraded 상태로 전환한다.
- pose inference가 밀릴 경우 detection과 alerting을 우선 유지하고, overlay 생성은 후순위로 미룬다.

## 모델 계층 예산
- detection: 가장 높은 우선순위
- event extraction: 항상 유지
- pose overlay rendering: 가장 낮은 우선순위
- classifier는 rules baseline이 안정화된 뒤에만 추가한다.

## 설정 초안
```yaml
edge_runtime:
  ingest_fps: 1.0
  max_ingest_fps: 2.0
  detection_target_latency_ms: 300
  alert_latency_budget_seconds: 15
  storage_high_watermark_ratio: 0.80
  healthcheck_stale_frame_seconds: 15
  degraded_pose_queue_size: 10
```

## 이유
- 희귀 이벤트 탐지에서는 모든 프레임을 고속 처리하는 것보다 안정적인 장시간 운영이 더 중요하다.
- detection과 event extraction이 살아 있으면 데이터 수집과 기본 경보 기능을 유지할 수 있다.
- 저장과 overlay는 중요하지만, 실시간 alert보다 우선순위가 낮다.

## 측정 항목
- average detection latency
- 95p detection latency
- pose job queue depth
- alert send success rate
- disk usage ratio
- temperature
- daily false positive count
- weekly missed-event review count

## 승격 기준
다음 조건을 만족할 때만 FPS나 모델 복잡도를 올린다.

- 하루 이상 안정적으로 실행
- 알림 누락이 시스템 과부하 때문이 아님
- 온도/메모리 압박이 관리 가능
- 이벤트 저장 누락이 없음

## 후속 작업
- 실제 Pi 5에서 baseline latency 측정
- healthcheck schema 추가
- edge runtime 설정을 `configs`로 분리
