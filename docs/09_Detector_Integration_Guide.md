# 09. Detector Integration Guide

## 목적
실제 개 탐지 모델을 WatchDog 파이프라인에 연결하기 위한 최소 규약을 정리한다.

## 현재 지원 백엔드
- `mock`
- `opencv_dnn`
- `hailo_hef`

## 추천 백엔드
라즈베리파이 5 + AI HAT+ 환경에서는 `hailo_hef`를 우선 추천한다.

추천 기본 모델:
- `/usr/share/hailo-models/yolov8s_h8l.hef`
- 라벨 파일: `configs/dog_labels.coco.txt`

## `opencv_dnn` 백엔드 규약
다음 조건 중 하나를 만족하는 모델을 우선 대상으로 한다.

1. OpenCV `cv2.dnn.readNet(...)`로 로드 가능
2. 출력이 detection row 리스트로 해석 가능

row 형식은 아래를 기대한다.

```text
[x1, y1, x2, y2, confidence, class_id]
```

- 좌표는 원본 이미지 픽셀 좌표
- `confidence`는 0~1
- `class_id`는 `labels_path`의 line index 기준

## 권장 파일 배치
```text
models/
  detector.onnx
  detector.cfg              # 선택
  dog_labels.txt
```

## 설정 예시
```yaml
detection:
  backend: opencv_dnn
  confidence_threshold: 0.50
  model_path: models/detector.onnx
  config_path:
  labels_path: configs/dog_labels.example.txt
  dog_class_names:
    - dog
  input_width: 640
  input_height: 640
  scale_factor: 0.00392156862745098
  swap_rb: true
```

## 1차 점검 절차
1. `python scripts/check_camera.py --config configs/app.rpi.camera.yaml`
2. 저장된 `exports/camera_check.jpg` 확인
3. detection 설정을 `opencv_dnn`으로 변경
4. 아래 명령으로 snapshot 테스트

```bash
python scripts/detect_snapshot.py --config configs/app.rpi.camera.yaml --image exports/camera_check.jpg
```

## 기대 결과
- 최소 1개의 `dog` detection이 JSON으로 출력
- confidence와 bbox가 합리적인 범위

## 문제 발생 시 먼저 확인할 것
- `.venv`에서 `cv2` import 가능 여부
- `model_path` 파일 존재 여부
- `labels_path`의 `dog` class index 일치 여부
- 모델 출력이 row 형식과 맞는지

## 주의
모든 ONNX detector가 바로 이 형식으로 맞지는 않는다. 출력 형식이 다르면 `OpenCVDnnDogDetector._decode_outputs`를 모델에 맞게 조정해야 한다.

## `hailo_hef` 백엔드 규약
현재 구현은 Hailo에서 postprocess가 포함된 YOLO NMS 출력 HEF를 기대한다.

권장 설정:
```yaml
detection:
  backend: hailo_hef
  confidence_threshold: 0.40
  model_path: /usr/share/hailo-models/yolov8s_h8l.hef
  config_path:
  labels_path: configs/dog_labels.coco.txt
  dog_class_names:
    - dog
  input_width: 640
  input_height: 640
  scale_factor: 0.00392156862745098
  swap_rb: true
  stream_interface: PCIe
```

`hailo parse-hef /usr/share/hailo-models/yolov8s_h8l.hef` 기준으로 이 모델은 이미 `yolov8_nms_postprocess` 출력을 포함한다.

## Hailo 점검 절차
1. `hailortcli scan`
2. `ls -l /dev/hailo*`
3. `python scripts/check_camera.py --config configs/app.rpi.camera.yaml`
4. detection 설정을 `hailo_hef`로 변경
5. 아래 명령으로 snapshot 테스트

```bash
python scripts/detect_snapshot.py --config configs/app.rpi.camera.yaml --image exports/camera_check.jpg
```

## 현재 확인된 리스크
- PCI 장치는 스캔되더라도 `/dev/hailo0`가 없으면 Python 추론이 열리지 않는다.
- 이 경우 드라이버/서비스 상태를 먼저 해결해야 한다.
