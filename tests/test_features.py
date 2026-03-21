from app.core.schemas import Keypoint, PoseFrame
from app.events.models import EventWindow
from app.features.extractor import FeatureExtractor
from app.ingest.frame_source import Frame


def test_feature_extraction_is_deterministic() -> None:
    event = EventWindow(event_id="e1", start_s=0.0, end_s=12.0, frames=[Frame(index=i, timestamp_s=float(i)) for i in range(13)])
    pose_frames = [
        PoseFrame(timestamp_s=0.0, keypoints=[Keypoint("nose",0,0.5,0.9), Keypoint("shoulder",0,0.7,0.9), Keypoint("hip",0,0.8,0.9)]),
        PoseFrame(timestamp_s=1.0, keypoints=[Keypoint("nose",0,0.45,0.9), Keypoint("shoulder",0,0.62,0.9), Keypoint("hip",0,0.74,0.9)]),
        PoseFrame(timestamp_s=2.0, keypoints=[Keypoint("nose",0,0.5,0.9), Keypoint("shoulder",0,0.69,0.9), Keypoint("hip",0,0.79,0.9)]),
    ]
    features = FeatureExtractor().extract(event, pose_frames)
    assert features.duration_s == 12.0
    assert features.attempt_count >= 1
    assert features.body_lift_ratio > 0
