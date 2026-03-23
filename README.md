# Dog Rise Alert Project Skeleton

노견이 **일어나고 싶어도 제대로 일어나지 못하는 상황**을 CCTV 영상 기반으로 감지하고,
메신저 알림을 보내기 위한 Python 프로젝트 골격입니다.

이 저장소는 다음을 포함합니다.
- 모듈별 디렉터리 구조
- mock 기반 end-to-end 파이프라인
- 이벤트/포즈/특징/룰 엔진 기본 스키마
- 이벤트별 clip/snapshot/metadata 저장
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
python scripts/check_camera.py --config configs/app.rpi.camera.yaml
python scripts/detect_snapshot.py --config configs/app.rpi.camera.yaml --image exports/camera_check.jpg
python scripts/export_review_queue.py --config configs/app.example.yaml
python scripts/import_review_labels.py --config configs/app.example.yaml --manifest exports/review_export/review_manifest.csv
python scripts/train_classifier.py --config configs/app.example.yaml
```

실카메라 입력을 쓰려면 `configs/app.example.yaml`의 `ingest.backend`를 `opencv` 또는 `picamera2`로 바꾸면 됩니다. 라즈베리파이 Camera Module v3는 `picamera2` 경로가 우선이며, 초기 운영용 예시는 `configs/app.rpi.camera.yaml`에 추가되어 있습니다. AI HAT+ 환경에서는 detector를 `hailo_hef`로 두고 `/usr/share/hailo-models/yolov8s_h8l.hef` 같은 HEF 모델을 우선 추천합니다.

## 현재 구현 상태
- 실제 카메라 입력: OpenCV `VideoCapture` 기반 로컬 카메라 소스 제공
- Raspberry Pi Camera Module 입력: `picamera2` 기반 소스 제공
- AI HAT+ detector 입력: `hailo_hef` 기반 HEF 모델 경로 지원
- 실제 dog detector: OpenCV DNN adapter 골격 제공, 기본 설정은 mock
- ROI 기반 motion gate: frame difference 기반 경량 게이트 제공
- 실제 pose estimator: 미구현(wrapper 자리만 제공)
- 이벤트 저장: `artifacts/<event_id>/clip.mp4`, `snapshot.jpg`, `metadata.json`
- review export: `exports/review_export/review_manifest.csv`, `review_manifest.jsonl`
- label import: reviewed CSV를 `exports/labels/clips.csv`와 event metadata에 반영
- classifier dataset loader: reviewed labels와 feature dataset을 `event_id`로 결합
- baseline classifier: nearest-prototype 모델을 `exports/models/prototype_classifier.json`으로 저장
- detector snapshot check: 저장된 카메라 이미지에 detector를 단독 실행 가능
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
5. reviewed dataset 기반 baseline classifier 추가
