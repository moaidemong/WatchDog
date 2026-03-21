# 05. Notification and Deployment

## 1. 알림 목표
알림은 "단순히 탐지 결과를 보내는 것"이 아니라, 사용자가 즉시 상황을 파악하고 행동할 수 있도록 설계해야 한다.

## 2. 알림 채널 후보
- Telegram
- Slack
- Discord
- Kakao Work
- 이메일
- SMS (후순위)
- Home Assistant push

1차 추천:
- 개인 사용이면 Telegram 또는 Discord
- 이미 쓰는 업무 메신저가 있으면 Slack/Kakao Work

## 3. 알림 메시지 구성
권장 메시지:
- 이벤트 유형
- 카메라명
- 발생 시각
- 점수
- 짧은 설명
- 스냅샷
- 클립 링크 또는 파일
- 재알림 여부

예시:
```text
[Dog Rise Alert]
카메라: livingroom_01
시각: 2026-03-20 22:14:03
이벤트: 기상 실패 의심
점수: 0.91
설명: 12초 동안 3회 기상 시도, standing 전이 실패
```

## 4. 중복 알림 억제
중요:
같은 사건으로 알림이 폭주하면 시스템은 곧 꺼지게 된다.

권장 정책:
- 동일 카메라, 동일 구역, 동일 이벤트 유형에 대해 cooldown 적용
- alert state 유지 중에는 요약 업데이트만 전송
- 회복 감지 시 "resolved" 메시지 선택적 전송

예:
- 첫 알림
- 3분 이내 동일 사건은 억제
- 5분 뒤에도 지속되면 재알림

## 5. 이벤트 저장 정책
각 알림에는 아래가 저장되어야 한다.
- snapshot
- short clip
- pose overlay clip (선택)
- inference metadata
- alert delivery result

## 6. 배포 형태
### 6.1 로컬 단일 머신
구성:
- Python services
- SQLite
- local file storage

장점:
- 단순
- 시작이 빠름

### 6.2 Docker Compose
구성 예:
- app
- db
- notifier
- optional mqtt broker
- optional frigate

장점:
- 재현성
- 관리 편리

### 6.3 분리형 운영
- Frigate host
- Inference host
- NAS storage

장점:
- 실운영 확장성

## 7. Docker Compose 예시 개념
```yaml
services:
  app:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
  db:
    image: postgres:16
  mqtt:
    image: eclipse-mosquitto
```

## 8. 운영 모드
### Development mode
- 파일 입력
- 샘플 클립 반복 추론
- notebook/CLI 중심

### Staging mode
- RTSP live input
- 로그 강화
- 실제 알림은 test channel

### Production mode
- 실카메라 운영
- 알림 실전송
- error handling
- health checks
- watchdog

## 9. 헬스체크
권장 체크 항목:
- 카메라 입력 살아있는지
- 마지막 프레임 수신 시각
- detection 루프 정상인지
- pose 추론 지연 여부
- notifier 실패 여부
- 디스크 용량
- DB 연결 상태

## 10. 보안/프라이버시
- RTSP 계정 분리
- 환경변수로 토큰 관리
- 이벤트 클립 저장 보존기간 설정
- 외부 메신저 전송 시 최소 데이터만 첨부
- 집 내부 영상이므로 접근 권한 관리 중요

## 11. 운영 추천안
1차 실전 운영 기준:
- Docker Compose
- local storage + periodic archive
- Telegram notifier
- SQLite 또는 PostgreSQL
- 오류 로그 파일 + 간단한 daily summary
