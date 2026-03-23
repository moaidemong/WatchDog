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
export TAPO_USERNAME=your_username
export TAPO_PASSWORD=your_password
python scripts/run_pipeline.py --config configs/app.tapo.multi.example.yaml --camera-id b
python scripts/run_pipeline.py --config configs/app.tapo.multi.example.yaml --camera-id c
bash scripts/run_tapo_priority.sh
bash scripts/run_tapo_priority.sh --loop
python -m pip install -e .[onvif]
python scripts/test_onvif_events.py --config configs/app.tapo.multi.example.yaml --camera-id b
python scripts/run_onvif_gated_pipeline.py --config configs/app.tapo.multi.example.yaml --camera-id b --wsdl-dir /tmp/python-onvif-zeep/wsdl
bash scripts/run_onvif_gated_service.sh b
python scripts/export_review_queue.py --config configs/app.example.yaml
python scripts/import_review_labels.py --config configs/app.example.yaml --manifest exports/review_export/review_manifest.csv
python scripts/train_classifier.py --config configs/app.example.yaml
```

실카메라 입력을 쓰려면 `configs/app.example.yaml`의 `ingest.backend`를 `opencv` 또는 `picamera2`로 바꾸면 됩니다. 라즈베리파이 Camera Module v3는 `picamera2` 경로가 우선이며, 초기 운영용 예시는 `configs/app.rpi.camera.yaml`에 추가되어 있습니다. AI HAT+ 환경에서는 detector를 `hailo_hef`로 두고 `/usr/share/hailo-models/yolov8s_h8l.hef` 같은 HEF 모델을 우선 추천합니다.

TAPO RTSP 다중 카메라는 `configs/app.tapo.multi.example.yaml` 예시를 사용하면 됩니다. RTSP 계정과 패스워드는 설정 파일에 직접 넣지 않고 `TAPO_USERNAME`, `TAPO_PASSWORD` 환경 변수로 주입하도록 구성돼 있습니다. 카메라 명칭은 `a/1 -> 192.168.219.111`, `b/2 -> 192.168.219.112`, `c/3 -> 192.168.219.113`으로 정리돼 있고, `--camera-id a`와 `--camera-id 1`처럼 별칭도 함께 사용할 수 있습니다.
현재 운영 우선순위는 주간/야간 모두 `b/2 -> c/3 -> a/1`입니다. `scripts/run_tapo_priority.sh`는 이 우선순위대로 세 카메라를 순차 실행합니다.
현재 `a` 저시점 샷에서는 detector가 노령견을 `horse`로 오인하는 경우가 있어, 예시 설정은 임시로 `dog_class_names: [dog, horse]`를 사용합니다.
ONVIF 이벤트 실험은 [test_onvif_events.py](/home/moai/Workspace/Codex/WatchDog/scripts/test_onvif_events.py)로 할 수 있습니다. 이 스크립트는 설정 파일의 RTSP 계정/호스트를 재사용해 해당 카메라의 ONVIF `PullPoint` 이벤트를 30초 동안 출력합니다.
실험용 서버-푸시 프로브는 [onvif_push_probe.py](/home/moai/Workspace/Codex/WatchDog/tools/experimental/onvif_push_probe.py)로 옮겨두었습니다. 현재 실전 경로는 Pull 기반이며, [run_onvif_gated_pipeline.py](/home/moai/Workspace/Codex/WatchDog/scripts/run_onvif_gated_pipeline.py)는 `IsPet=true` 또는 `IsMotion=true` 이벤트를 받아 cooldown 후 기존 RTSP/Hailo 파이프라인을 한 번 실행합니다.
장시간 운영용 래퍼인 [run_onvif_gated_service.sh](/home/moai/Workspace/Codex/WatchDog/scripts/run_onvif_gated_service.sh)는 5분 단위 ONVIF 재구독을 반복하는 `systemd` 템플릿 서비스에서 사용합니다. `a/b/c` 세 카메라의 ONVIF listener는 동시에 떠 있어도, 실제 RTSP/Hailo 파이프라인은 공용 lock 파일로 한 번에 하나만 실행되도록 맞춰져 있습니다.

`systemd` 운영은 단일 Hailo 장치를 안전하게 쓰기 위해 3개 카메라를 동시에 띄우지 않고 `b -> c -> a` 순환 방식으로 두는 것을 권장합니다. 예시 서비스 파일은 [watchdog-tapo-priority.service](/home/moai/Workspace/Codex/WatchDog/deploy/systemd/watchdog-tapo-priority.service)이고, 환경 변수 파일 예시는 [watchdog-tapo.env.example](/home/moai/Workspace/Codex/WatchDog/configs/watchdog-tapo.env.example)입니다.
RTSP/FFmpeg 계열 `stderr`는 프로젝트 루트의 [watchdog-tapo-priority.stderr.log](/home/moai/Workspace/Codex/WatchDog/watchdog-tapo-priority.stderr.log)로 빠지도록 구성돼 있어, `journalctl`에는 핵심 서비스 로그만 남도록 했습니다.
이벤트 드리븐 모드용 템플릿 서비스는 [watchdog-onvif-gated@.service](/home/moai/Workspace/Codex/WatchDog/deploy/systemd/watchdog-onvif-gated@.service)이며, 전체 카메라 묶음용 target은 [watchdog-onvif-gated.target](/home/moai/Workspace/Codex/WatchDog/deploy/systemd/watchdog-onvif-gated.target)입니다. 카메라별 `stderr`는 프로젝트 루트의 `watchdog-onvif-a.stderr.log`, `watchdog-onvif-b.stderr.log`, `watchdog-onvif-c.stderr.log`로 분리됩니다.

설치 예시:
```bash
cd /home/moai/Workspace/Codex/WatchDog
cp configs/watchdog-tapo.env.example configs/watchdog-tapo.env
sudo cp deploy/systemd/watchdog-tapo-priority.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now watchdog-tapo-priority.service
sudo systemctl status watchdog-tapo-priority.service --no-pager
journalctl -u watchdog-tapo-priority.service -f
tail -f logs/watchdog-tapo-priority.stderr.log
tail -f watchdog-tapo-priority.stderr.log
```

이벤트 드리븐 서비스 예시:
```bash
cd /home/moai/Workspace/Codex/WatchDog
cp configs/watchdog-tapo.env.example configs/watchdog-tapo.env
sudo cp deploy/systemd/watchdog-onvif-gated@.service /etc/systemd/system/
sudo cp deploy/systemd/watchdog-onvif-gated.target /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now watchdog-onvif-gated.target
sudo systemctl start watchdog-onvif-gated@a.service watchdog-onvif-gated@b.service watchdog-onvif-gated@c.service
sudo systemctl status watchdog-onvif-gated@a.service --no-pager
sudo systemctl status watchdog-onvif-gated@b.service --no-pager
sudo systemctl status watchdog-onvif-gated@c.service --no-pager
journalctl -u watchdog-onvif-gated@b.service -f
tail -f watchdog-onvif-b.stderr.log
```

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
- RTSP multi-camera input: `camera_id` 선택 기반 다중 카메라 설정 지원
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
