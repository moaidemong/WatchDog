from __future__ import annotations


REVIEW_STATUS_OPTIONS = ["pending", "approved", "rejected"]

REVIEW_LABEL_OPTIONS = [
    "failed_get_up_attempt",
    "slump_or_collapse",
    "restless_while_lying",
    "urination",
    "defecation",
    "normal_standing",
    "impaired_standing",
    "normal_rest",
    "normal_movement",
    "human_interference",
    "other_animal",
    "unclear",
]

TEXT_TRANSLATIONS = {
    "event_id": "이벤트 ID",
    "camera_id": "카메라",
    "captured_at": "캡처 시각",
    "duration_s": "지속 시간(초)",
    "frame_count": "프레임 수",
    "predicted_label": "자동 판정",
    "should_alert": "알림 후보",
    "decision_score": "디시전 스코어",
    "decision_reasons": "근거",
    "review_status": "검토 상태",
    "review_label": "검토 라벨",
    "review_notes": "메모",
    "clip": "클립",
    "snapshot": "스냅샷",
    "save": "저장",
    "sync": "동기화",
    "pending": "대기",
    "approved": "확정",
    "rejected": "기각",
    "failed_get_up_attempt": "기상 실패 시도",
    "slump_or_collapse": "주저앉음/무너짐",
    "restless_while_lying": "누운 채 불편 들썩임",
    "urination": "소변",
    "defecation": "대변",
    "normal_standing": "정상 기립",
    "impaired_standing": "불안정 기립",
    "normal_rest": "정상 휴식",
    "normal_movement": "정상 이동",
    "human_interference": "사람 개입",
    "other_animal": "다른 동물",
    "unclear": "애매함",
    "no_alert": "이상 없음",
    "multiple rise attempts detected": "여러 차례 기상 시도",
    "long-duration struggle": "장시간 버팀/힘겨움",
    "body lift effort observed": "몸을 들어올리려는 시도",
    "insufficient progress to standing": "일어서기 진전 부족",
}


def translate(key: str) -> str:
    return TEXT_TRANSLATIONS.get(key, key)
