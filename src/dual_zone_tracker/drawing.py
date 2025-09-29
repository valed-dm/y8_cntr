from typing import List

import cv2
import numpy as np
from numpy.typing import NDArray
from ultralytics.engine.results import Results

from .tracker import VehicleTracker
from .tracker import _to_numpy


ImageType = NDArray[np.uint8]
ColorTuple = tuple[int, int, int]


def draw_annotations(
    frame: ImageType,
    yolo_results: List[Results],
    tracker: VehicleTracker,
) -> ImageType:
    """
    Draws all annotations (boxes, labels, polygons, counter) on the frame.

    Args:
        frame: The original video frame to draw on.
        yolo_results: The list of results from the YOLO model for this frame.
        tracker: The VehicleTracker instance containing the current state.

    Returns:
        The annotated frame.
    """
    annotated_frame = frame.copy()

    if yolo_results[0].boxes is None or yolo_results[0].boxes.id is None:
        # Draw the UI elements even if there are no boxes
        _draw_ui(annotated_frame, tracker)
        return annotated_frame

    boxes_np = _to_numpy(yolo_results[0].boxes.xyxy)
    track_ids_np = _to_numpy(yolo_results[0].boxes.id)

    for box, track_id in zip(boxes_np, track_ids_np, strict=False):
        _draw_bounding_box(annotated_frame, box, int(track_id), tracker)

    # Draw the counter and polygons
    _draw_ui(annotated_frame, tracker)

    return annotated_frame


def _draw_bounding_box(
    frame: ImageType,
    box: NDArray[np.float32],
    track_id: int,
    tracker: VehicleTracker,
) -> None:
    """Draws a single bounding box and its corresponding label on the frame."""
    x1, y1, x2, y2 = map(int, box)

    label = f"ID: {track_id}"
    color: ColorTuple = (0, 255, 0)  # Default: Green

    if track_id in tracker.track_to_custom_id:
        label += f" | {tracker.track_to_custom_id[track_id]}"
        color = (255, 255, 255)  # Identified: White

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        label,
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )


def _draw_ui(frame: ImageType, tracker: VehicleTracker) -> None:
    """Draws static UI elements like the counter and polygons on the frame."""
    # Draw counter
    counter_text = f"Vehicles: {tracker.total_vehicle_count}"
    cv2.putText(
        frame,
        counter_text,
        (100, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )

    # Draw polygons
    for poly in tracker.polygons.values():
        pts = np.array(poly.exterior.coords, dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
