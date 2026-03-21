# 07. VSCode + ChatGPT 5.4 Working Guide

## 1. 목적
이 문서는 VSCode에서 ChatGPT 5.4와 협업할 때 프로젝트 진행 품질을 높이기 위한 실무 가이드다.

핵심은 "큰 요구를 한 번에 던지기"보다, **문서와 코드 경계를 분명히 나누고 작은 작업 단위로 반복**하는 것이다.

## 2. 기본 원칙
- 먼저 문서화, 다음에 코드화
- 추상적 요구보다 명시적 입출력 정의 우선
- 한 번에 한 모듈
- 항상 샘플 입력/출력 포함
- 평가 기준까지 같이 요청

## 3. 권장 협업 순서
1. 문제와 범위를 문서로 확정
2. 모듈 인터페이스 정의
3. 테스트 가능한 골격 생성
4. 더미 데이터로 동작 확인
5. 실제 데이터 연결
6. 리팩토링
7. 운영 스크립트 추가

## 4. 좋은 요청 방식
### 나쁜 예
- "전체 시스템 다 만들어줘"

### 좋은 예
- "RTSP 입력을 받아 10초 단위로 dog detection 이벤트 클립을 저장하는 Python 모듈을 만들어줘"
- "입력/출력 스키마와 tests를 함께 작성해줘"
- "실패 시 로그 포맷과 예외 처리까지 포함해줘"

## 5. 작업 단위 예시
### 예시 1. Ingest 모듈
요청:
- OpenCV 기반 RTSP reader
- reconnect logic
- frame timestamping
- unit-testable wrapper

### 예시 2. Event extractor
요청:
- dog detected frames 기반 event merge logic
- pre/post roll 적용
- metadata JSON 저장

### 예시 3. Feature extractor
요청:
- keypoint sequence 입력
- event-level features 계산
- pandas DataFrame 반환

## 6. 각 단계에서 ChatGPT 5.4에 같이 주면 좋은 정보
- 현재 파일 구조
- 사용할 Python 버전
- 입력 파일 예시
- 기대하는 JSON/CSV schema
- 현재까지의 제약사항
- 오류 로그
- 성능 병목
- refactor 대상 파일 전문

## 7. 프롬프트 템플릿
### 7.1 새 모듈 생성
```text
프로젝트: Dog Rise Alert

목적:
RTSP 입력에서 dog detection 결과를 받아 이벤트 클립을 생성하는 모듈을 만들고 싶다.

제약:
- Python 3.11
- OpenCV 사용
- 함수형보다 테스트하기 쉬운 클래스를 선호
- logging 포함
- data/events/{event_id} 구조로 저장

입력:
- detection timeline list[dict]

출력:
- clip metadata JSON
- event folder path

요청:
1. 설계 제안
2. production-ready Python 코드
3. pytest 테스트 코드
4. 향후 pose 추정 단계와 연결 포인트 설명
```

### 7.2 리팩토링
```text
아래 파일은 동작은 하지만 책임이 섞여 있다.
- event detection
- file IO
- logging
- notification

SOLID 관점에서 모듈을 분리해줘.
파일 전문:
...
```

### 7.3 디버깅
```text
다음 오류가 발생한다.
- 환경: Ubuntu 22.04 / Python 3.11 / OpenCV 4.x
- 증상: RTSP reconnect 이후 timestamp drift
- 기대 동작: reconnect 후에도 event time alignment 유지

관련 코드:
...
로그:
...
원인 후보와 수정안을 제시하고, 패치 형태로 보여줘.
```

## 8. 권장 파일 단위 진행
- `app/ingest/reader.py`
- `app/events/extractor.py`
- `app/pose/infer.py`
- `app/features/event_features.py`
- `app/rules/failed_rise.py`
- `app/notify/telegram.py`
- `tests/...`

한 번에 여러 파일을 요청하더라도, 핵심 엔트리 파일부터 우선 구현하게 한다.

## 9. 검증 습관
ChatGPT 5.4가 코드를 작성한 뒤 항상 아래를 요청한다.
- edge case 설명
- 단위 테스트
- logging 포인트
- type hints
- 실패 처리
- TODO 목록

## 10. 협업 팁
- 긴 코드보다 먼저 설계를 받는다.
- 설계가 마음에 들면 그 설계대로 코드 생성.
- 불만족 시 "전체 재작성"보다 "책임 분리" 기준으로 수정 지시.
- 성능 이슈는 반드시 profiling 근거와 함께 논의.
- 실행 환경을 명확히 적는다.

## 11. 회의록/결정 기록
프로젝트 루트에 아래 파일을 유지하면 좋다.
- `docs/decisions/DECISION-0001-camera-topology.md`
- `docs/decisions/DECISION-0002-pose-framework.md`
- `docs/decisions/DECISION-0003-alert-thresholds.md`

## 12. 무엇을 먼저 맡기면 좋은가
- boilerplate
- schema
- tests
- CLI tools
- config loader
- feature extraction
- documentation

## 13. 무엇은 사람이 최종 결정해야 하는가
- positive label 정의
- 카메라 위치
- 운영 threshold
- 실전 경보 정책
- 개인정보/영상 보관 정책
