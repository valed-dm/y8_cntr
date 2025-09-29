import json
from pathlib import Path
from typing import Dict
from typing import cast

import cv2
from shapely.geometry import Polygon
from ultralytics import YOLO

from dual_zone_tracker import settings
from dual_zone_tracker.drawing import ImageType
from dual_zone_tracker.drawing import draw_annotations
from dual_zone_tracker.tracker import VehicleTracker


def load_polygons_from_json(config_path: Path) -> Dict[str, Polygon]:
    """Loads polygon coordinates from a JSON file."""
    with open(config_path, "r") as f:
        data = json.load(f)
    return {name: Polygon(coords) for name, coords in data.items()}


def main() -> None:
    """Main function to orchestrate the vehicle tracking process."""
    model = YOLO(settings.MODEL_PATH)
    polygons = load_polygons_from_json(settings.POLYGON_CONFIG_PATH)

    cap = cv2.VideoCapture(str(settings.VIDEO_PATH))
    if not cap.isOpened():
        print(f"FATAL ERROR: Could not open video file: {settings.VIDEO_PATH}")
        return

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    out = cv2.VideoWriter(
        str(settings.OUTPUT_VIDEO_PATH), fourcc, fps, (frame_w, frame_h)
    )

    tracker = VehicleTracker(polygons=polygons)
    print("Starting video processing...")

    while cap.isOpened():
        ret, frame_from_cv = cap.read()
        if not ret or frame_from_cv is None:
            print("End of video stream or failed to read frame.")
            break

        frame = cast(ImageType, frame_from_cv)

        yolo_results = model.track(
            frame, persist=True, conf=settings.CONFIDENCE_THRESHOLD, verbose=False
        )
        tracker.update(yolo_results)
        annotated_frame = draw_annotations(frame, yolo_results, tracker)

        cv2.imshow("Dual View Tracker", annotated_frame)
        out.write(annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Processing complete. Video saved to: {settings.OUTPUT_VIDEO_PATH}")


if __name__ == "__main__":
    main()
