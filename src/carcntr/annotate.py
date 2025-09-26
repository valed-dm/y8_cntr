import json
from pathlib import Path

import cv2


VIDEO_PATH = Path("data/counting_cars.mp4")
OUTPUT_FRAME_PATH = Path("data/first_frame.jpg")
CONFIG_PATH = Path("config/polygons.json")


def capture_frame(video_path: Path, frame_no: int = 0) -> Path:
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError(f"Could not read frame {frame_no} from {video_path}")

    OUTPUT_FRAME_PATH.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT_FRAME_PATH), frame)
    return OUTPUT_FRAME_PATH


def annotate_polygon(
    image_path: Path,
    window_name: str = "Polygon Picker",
) -> list[tuple[int, int]]:
    img = cv2.imread(str(image_path))
    clone = img.copy()
    points: list[tuple[int, int]] = []

    def click_event(event, x, y, flags, param):
        nonlocal points, img
        if event == cv2.EVENT_LBUTTONDOWN:  # left-click
            points.append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            if len(points) > 1:
                cv2.line(img, points[-2], points[-1], (0, 255, 0), 2)
        elif event == cv2.EVENT_RBUTTONDOWN:  # right-click = undo
            if points:
                points.pop()
                img = clone.copy()
                for i, pt in enumerate(points):
                    cv2.circle(img, pt, 5, (0, 255, 0), -1)
                    if i > 0:
                        cv2.line(img, points[i - 1], pt, (0, 255, 0), 2)

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, click_event)

    while True:
        cv2.imshow(window_name, img)
        key = cv2.waitKey(1) & 0xFF

        if key == 13:
            break
        elif key == 27:
            points = []
            break

    cv2.destroyAllWindows()
    return points


def main():
    frame_path = capture_frame(VIDEO_PATH, frame_no=100)
    print(f"Frame saved to: {frame_path}")
    print(
        "Draw RED polygon (counting zone)."
        " Left click = add point,"
        " Right click = undo,"
        " Enter = finish"
    )
    red_polygon = annotate_polygon(frame_path, "Red Polygon")

    print(
        "Draw GREEN polygon (secondary zone)."
        " Left click = add point,"
        " Right click = undo,"
        " Enter = finish"
    )
    green_polygon = annotate_polygon(frame_path, "Green Polygon")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"red_zone": red_polygon, "green_zone": green_polygon}, f, indent=2)

    print(f"Polygons saved to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
