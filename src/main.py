import cv2
import numpy as np
from loguru import logger
from shapely.geometry import Point
from ultralytics import YOLO

from src.carcntr.counting import CounterManager
from src.carcntr.utils import load_zones


VIDEO_PATH = "../data/counting_cars.mp4"
POLYGON_PATH = "../config/polygons.json"
MODEL_PATH = "yolov8n.pt"
OUTPUT_VIDEO_PATH = "output.mp4"
STATS_FILE_PATH = "statistics.json"
CONFIDENCE_THRESHOLD = 0.7
VEHICLE_CLASS_IDS = [2, 5, 7]


def main():
    logger.info("Starting Car Counter Application")
    model = YOLO(MODEL_PATH)
    red_zone, green_zone = load_zones(POLYGON_PATH)
    cap = cv2.VideoCapture(VIDEO_PATH)

    counter_manager = CounterManager()

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (frame_width, frame_height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logger.info("End of video stream.")
            break

        results = model.track(
            frame,
            persist=True,
            conf=CONFIDENCE_THRESHOLD,
            classes=VEHICLE_CLASS_IDS,
            verbose=False,
        )

        if results[0].boxes.id is None:
            out.write(frame)
            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        tracked_objects_in_red_zone = []
        for box_data in results[0].boxes.data:
            center_x = (box_data[0] + box_data[2]) / 2
            center_y = (box_data[1] + box_data[3]) / 2
            if red_zone.contains(Point(center_x, center_y)):
                tracked_objects_in_red_zone.append(box_data)

        counter_manager.update(tracked_objects_in_red_zone, green_zone)

        for obj in tracked_objects_in_red_zone:
            x1, y1, x2, y2, track_id, _, _ = obj
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"ID:{int(track_id)}"
            cv2.putText(
                frame,
                label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        current_counts = counter_manager.get_current_counts()
        display_text = f"Total Vehicles: {current_counts['total']}"
        cv2.putText(
            frame,
            display_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )

        cv2.polylines(
            frame,
            [np.array(red_zone.exterior.coords, dtype=np.int32)],
            isClosed=True,
            color=(0, 0, 255),
            thickness=2,
        )
        cv2.polylines(
            frame,
            [np.array(green_zone.exterior.coords, dtype=np.int32)],
            isClosed=True,
            color=(0, 255, 0),
            thickness=2,
        )

        out.write(frame)
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    counter_manager.save_statistics(STATS_FILE_PATH)
    logger.info(f"Processing complete. Output video saved to: {OUTPUT_VIDEO_PATH}")


if __name__ == "__main__":
    main()
