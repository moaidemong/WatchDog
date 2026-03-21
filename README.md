# Dog Rise Alert Project Skeleton

노견이 **일어나고 싶어도 제대로 일어나지 못하는 상황**을 CCTV 영상 기반으로 감지하고,
메신저 알림을 보내기 위한 Python 프로젝트 골격입니다.

이 저장소는 다음을 포함합니다.
- 모듈별 디렉터리 구조
- mock 기반 end-to-end 파이프라인
- 이벤트/포즈/특징/룰 엔진 기본 스키마
- 알림 중복 억제 로직
- pytest 기반 최소 테스트
- VSCode 설정 예시
- 문서 세트(`docs/`)

## 빠른 시작

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
pytest
python scripts/run_pipeline.py --config configs/app.example.yaml
```

## 현재 구현 상태
- 실제 CCTV 연동: 미구현(인터페이스와 mock만 제공)
- 실제 dog detector: 미구현(wrapper 자리만 제공)
- 실제 pose estimator: 미구현(wrapper 자리만 제공)
- notifier: stdout / telegram stub
- API: 상태 확인용 최소 FastAPI 엔드포인트

## 핵심 구조
- `app/ingest/` : 카메라/프레임 입력
- `app/detection/` : dog detection wrapper
- `app/events/` : 프레임 → 이벤트 구간 병합
- `app/pose/` : 포즈 추정 wrapper
- `app/features/` : 이벤트 수준 특징 추출
- `app/rules/` : 기상 실패 룰 엔진
- `app/notify/` : 메신저 전송
- `app/pipeline/` : 전체 오케스트레이션
- `tests/` : 핵심 순수 로직 테스트

## 권장 다음 작업
1. `MockDogDetector`를 실제 detector로 교체
2. `MockPoseEstimator`를 실제 pose wrapper로 교체
3. 이벤트 검토 UI 또는 review export 추가
4. 수집 클립 기준 라벨링 세트 축적
5. 룰 엔진 기준선 확보 후 classifier 추가
