# AGENTS.md

이 문서는 VSCode에서 ChatGPT 5.4 또는 유사한 AI 코딩 어시스턴트와 협업할 때, 이 저장소에서 따라야 할 기본 규칙을 정의한다.

## 1. 프로젝트 요약
프로젝트명: Dog Rise Alert

목표:
- 노견이 일어나고 싶어도 일어나지 못하는 상황을 CCTV 기반으로 감지
- 메신저로 신속하게 알림
- 적은 샘플로 가능한 구조 선택
- explainable pipeline 유지

핵심 전략:
- dog detection
- pose estimation
- temporal feature extraction
- rule engine + small classifier
- event review + active learning

## 2. 절대 원칙
1. 처음부터 end-to-end video classifier를 기본안으로 강요하지 말 것.
2. 가능한 한 해석 가능한 중간 표현을 유지할 것.
3. 라벨 정의가 모호하면 코드보다 먼저 라벨 규칙을 문서화할 것.
4. frame 단위가 아니라 event 단위를 기본 분석 단위로 볼 것.
5. production-ready 코드를 작성하되 과도한 복잡화는 피할 것.
6. 함수와 클래스는 테스트 가능하게 분리할 것.

## 3. 코딩 스타일
- Python 3.11+
- type hints 사용
- dataclass 적극 사용
- logging 사용
- 예외 처리 명시
- I/O와 순수 로직 분리
- 설정은 `configs/*.yaml` 또는 환경변수로 분리

## 4. 우선 구현 순서
1. ingest
2. dog detection event extraction
3. review/export utilities
4. pose inference wrapper
5. feature extraction
6. rule engine
7. notifier
8. classifier training/evaluation
9. API/UI

## 5. 디렉터리 책임
- `app/ingest/` : 카메라 입력, reconnect, timestamps
- `app/detection/` : dog detection wrappers
- `app/events/` : event merging, clip export, metadata
- `app/pose/` : pose model wrappers and output normalization
- `app/features/` : event-level features from pose series
- `app/rules/` : explicit behavior rules and score logic
- `app/classifier/` : training/inference for event classifier
- `app/notify/` : messenger integrations
- `app/storage/` : file/db persistence
- `app/api/` : optional REST API

## 6. 답변 방식 지침
AI assistant는 다음 형식을 선호한다.
1. 먼저 설계 요약
2. 그 다음 코드
3. 필요 시 테스트
4. 마지막에 edge cases / next steps

긴 파일을 생성할 때는:
- 책임 구분이 명확해야 한다.
- 숨겨진 전역 상태를 피한다.
- mock 가능한 인터페이스를 제공한다.

## 7. 금지 사항
- 라벨 정의를 임의로 바꾸지 말 것
- train/test leakage를 유발하는 예시 코드를 쓰지 말 것
- hard-coded secrets를 넣지 말 것
- event review 없이 자동 라벨을 truth로 간주하지 말 것
- "나중에 고치자" 식으로 중요한 예외 처리를 생략하지 말 것

## 8. 우선 작성할 유틸
- config loader
- event metadata schema
- clip saver
- pose sequence schema
- feature schema validation
- alert deduplicator
- evaluation report generator

## 9. 테스트 전략
최소한 아래 테스트를 포함한다.
- event merge logic
- cooldown logic
- feature extraction deterministic behavior
- rules threshold behavior
- malformed input handling

## 10. 모델 관련 원칙
- 1차는 rules-first
- 2차는 classical ML
- 3차만 sequence DL 검토
- 항상 baseline과 비교
- 성능 향상 근거 없이 복잡한 모델 도입 금지

## 11. 운영 관련 원칙
- 이벤트 저장은 재학습 자산이다.
- 알림은 중복 억제가 중요하다.
- 운영 로그는 사람이 읽을 수 있어야 한다.
- explainable metadata를 함께 저장한다.

## 12. 요청을 받을 때 우선 확인할 것
- 입력 스키마가 무엇인지
- 출력 스키마가 무엇인지
- 모듈의 책임이 어디까지인지
- 테스트 가능한 형태인지
- 실제 운영 환경 제약이 무엇인지
