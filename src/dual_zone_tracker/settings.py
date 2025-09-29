from pathlib import Path
from typing import Dict
from typing import Tuple
from typing import TypedDict


ColorTuple = Tuple[int, int, int]


class ZoneConfig(TypedDict):
    name: str
    color: ColorTuple


# --- Project Root ---
PROJECT_ROOT = Path(__file__).parent.parent.parent

# --- Path Definitions ---
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_DIR = PROJECT_ROOT / "src"

# --- File Paths ---
VIDEO_PATH = DATA_DIR / "video_obzor_new_cam_yos_2.avi"
MODEL_PATH = SRC_DIR / "model_only_car.pt"
POLYGON_CONFIG_PATH = CONFIG_DIR / "dual_view_polygons.json"
OUTPUT_VIDEO_PATH = OUTPUT_DIR / "output_dual_video.mp4"

# --- Model & Tracking Parameters ---
CONFIDENCE_THRESHOLD = 0.5

# --- Zone Names ---
ZONE_A_COUNTING = "zone_a_counting"
ZONE_TRIGGER_LEFT = "zone_trigger_left_lane"
ZONE_TRIGGER_RIGHT = "zone_trigger_right_lane"
ZONE_DESTINATION_LEFT = "zone_destination_left_lane"
ZONE_DESTINATION_RIGHT = "zone_destination_right_lane"

# --- Annotation Script Settings ---
FRAME_TO_CAPTURE = 50
ANNOTATION_FRAME_PATH = DATA_DIR / "annotation_frame.jpg"

ZONES_TO_ANNOTATE: Dict[str, ZoneConfig] = {
    "zone_a_counting": {
        "name": "1. Main Counting Zone (Left View, Both Lanes)",
        "color": (255, 0, 0),
    },
    "zone_trigger_left_lane": {
        "name": "2. Trigger Zone (Left Lane in Left View)",
        "color": (0, 0, 255),
    },
    "zone_trigger_right_lane": {
        "name": "3. Trigger Zone (Right Lane in Left View)",
        "color": (0, 165, 255),
    },
    "zone_destination_left_lane": {
        "name": "4. Destination Zone (Left Lane in Right View)",
        "color": (0, 255, 0),
    },
    "zone_destination_right_lane": {
        "name": "5. Destination Zone (Right Lane in Right View)",
        "color": (0, 255, 255),
    },
}
