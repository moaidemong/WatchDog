# DECISION-0002: Camera Placement and ROI

## 상태
Accepted

## 배경
이 프로젝트는 적은 샘플로 동작해야 하므로, 모델 복잡도보다 카메라 위치와 장면 일관성이 더 중요하다. Camera Module v3는 충분한 화질을 제공하지만, 설치 위치가 흔들리면 라벨 품질과 threshold 안정성이 함께 무너질 수 있다.

## 결정
카메라 설치와 ROI 운영 기준을 아래처럼 고정한다.

## 설치 원칙
- 1차는 반려견이 가장 오래 머무는 휴식 구역 1곳을 우선 감시한다.
- 카메라는 천장 모서리 또는 벽 상단에서 아래로 내려다보는 각도를 사용한다.
- 바닥 면적보다 반려견의 자세 변화가 잘 보이는 구도를 우선한다.
- 침구, 쿠션, 가구 다리로 인한 가림이 최소가 되도록 위치를 정한다.
- 카메라 위치를 정한 뒤에는 학습 기간 동안 가능한 한 이동하지 않는다.

## 프레이밍 원칙
- 반려견이 자주 눕는 구역이 화면 중앙 또는 중앙 하단에 오게 한다.
- 바닥 경계선, 매트, 침대 가장자리처럼 자세 변화를 비교할 수 있는 기준선이 보이게 한다.
- 보호자 이동 공간이나 문 입구는 필요 최소한만 포함한다.
- 역광이나 야간 IR 반사가 심한 면은 피한다.

## ROI 원칙
- 1차는 전체 화면을 처리하되, 휴식 구역 ROI를 별도 설정값으로 저장한다.
- motion gate와 detection crop은 ROI 안에서 먼저 평가한다.
- review metadata에는 `camera_id`, `roi_id`, `roi_bbox`를 함께 남긴다.
- 장기적으로는 ROI별 threshold 분리 가능성을 열어 둔다.

## 권장 검증 체크리스트
- 낮/밤 모두 반려견의 머리, 몸통, 앞다리, 엉덩이 축이 구분되는가
- 기상 시도 시 몸통 상승이 화면에서 명확히 보이는가
- 담요, 쿠션, 식탁 의자 등 주요 가림 요소가 반복적으로 keypoint를 가리는가
- 사람 개입 시 반려견이 완전히 가려지는가
- 20초 이상 연속 관찰 시 exposure 변동이 심하지 않은가

## 운영 메타데이터
카메라 설정 문서에는 최소 아래를 기록한다.

- camera_id
- physical_location
- mounting_height
- tilt_angle
- main_resting_zone
- roi_bbox
- day_mode_resolution
- night_mode_resolution
- fps

## 이유
- 이 프로젝트의 positive 정의는 body lift, repeated attempt, standing transition 관찰에 의존한다.
- 따라서 전신 또는 핵심 body axis가 안정적으로 보이는 시점이 중요하다.
- 고정된 카메라 환경은 적은 샘플에서도 threshold와 feature 분포를 안정화한다.

## 후속 작업
- 카메라 설치 후 샘플 이미지 30장 확보
- 낮/밤 샘플 각각에 대해 pose 가능 여부 검토
- ROI 설정 파일 초안 추가
