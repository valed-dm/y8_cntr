import json
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from dual_zone_tracker import settings


PointTuple = Tuple[int, int]
PolygonPoints = List[PointTuple]
ColorTuple = Tuple[int, int, int]
ImageType = NDArray[np.uint8]


class Annotator:
    """A class to handle the process of annotating polygons on a video frame."""

    def __init__(self) -> None:
        self.canvas_image: Union[ImageType, None] = None
        self.collected_polygons: Dict[str, PolygonPoints] = {}

    def run(self) -> None:
        """Orchestrates the entire annotation workflow."""
        print("Starting annotation process...")
        if not self._capture_frame():
            return
        if not self._collect_polygons():
            return
        self._save_polygons()
        self._show_final_preview()
        print("Annotation process completed successfully.")

    def _capture_frame(self) -> bool:
        """Captures a specific frame from the video and loads it onto the canvas."""
        if not settings.VIDEO_PATH.exists():
            print(f"Error: Video file not found at {settings.VIDEO_PATH}")
            return False
        cap = cv2.VideoCapture(str(settings.VIDEO_PATH))
        if not cap.isOpened():
            print(f"Error: Could not open video file: {settings.VIDEO_PATH}")
            return False
        cap.set(cv2.CAP_PROP_POS_FRAMES, settings.FRAME_TO_CAPTURE)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            print(f"Error: Could not read frame {settings.FRAME_TO_CAPTURE}.")
            return False
        settings.ANNOTATION_FRAME_PATH.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(settings.ANNOTATION_FRAME_PATH), frame)
        self.canvas_image = cast(ImageType, frame)
        print(f"Successfully captured frame to: {settings.ANNOTATION_FRAME_PATH}")
        return True

    def _collect_polygons(self) -> bool:
        """Loops through the required zones and gets user input for each polygon."""
        if self.canvas_image is None:
            print("Error: Cannot collect polygons, canvas image is not loaded.")
            return False
        for key, props in settings.ZONES_TO_ANNOTATE.items():
            window_name = str(props["name"])
            color = props["color"]
            points, updated_canvas = self._get_single_polygon(
                self.canvas_image, window_name, color
            )
            if not points:
                print(f"Annotation for '{window_name}' was cancelled. Aborting.")
                return False
            self.collected_polygons[key] = points
            self.canvas_image = updated_canvas
            print(f"'{window_name}' saved.")
        return True

    @staticmethod
    def _get_single_polygon(
        image: ImageType, window_name: str, color: ColorTuple
    ) -> Tuple[PolygonPoints, ImageType]:
        """Handles the UI for drawing one polygon."""
        clone = image.copy()
        current_drawing = image.copy()
        points: PolygonPoints = []

        def mouse_callback(event: int, x: int, y: int, flags: int, param: Any) -> None:
            nonlocal points, current_drawing
            if event == cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                cv2.circle(current_drawing, (x, y), 5, color, -1)
                if len(points) > 1:
                    cv2.line(current_drawing, points[-2], points[-1], color, 2)
            elif event == cv2.EVENT_RBUTTONDOWN and points:
                points.pop()
                current_drawing = clone.copy()
                for i, pt in enumerate(points):
                    cv2.circle(current_drawing, pt, 5, color, -1)
                    if i > 0:
                        cv2.line(current_drawing, points[i - 1], pt, color, 2)

        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, mouse_callback)
        print(f"\n--- Drawing '{window_name}' ---")
        print(
            "Left-click: Add point | Right-click: Undo | ENTER: Confirm | ESC: Cancel"
        )
        while True:
            cv2.imshow(window_name, current_drawing)
            key = cv2.waitKey(1) & 0xFF
            if key == 13:
                if len(points) > 1:
                    cv2.line(current_drawing, points[-1], points[0], color, 2)
                break
            if key == 27:
                points = []
                current_drawing = image.copy()
                break
        cv2.destroyAllWindows()
        return points, current_drawing

    def _save_polygons(self) -> None:
        """Saves the collected polygon data to a JSON file."""
        settings.POLYGON_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.POLYGON_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.collected_polygons, f, indent=4)
        print(f"\n✅ All polygons saved to {settings.POLYGON_CONFIG_PATH}")

    def _show_final_preview(self) -> None:
        """Displays the final image with all drawn polygons."""
        if self.canvas_image is not None:
            print("Showing final preview. Press any key to exit.")
            cv2.imshow("Final Result - All Polygons", self.canvas_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


if __name__ == "__main__":
    annotator = Annotator()
    annotator.run()
