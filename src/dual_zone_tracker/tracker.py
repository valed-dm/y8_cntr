import random
import string
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import TypedDict
from typing import Union
from typing import cast

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import Point
from shapely.geometry import Polygon
from torch import Tensor
from ultralytics.engine.results import Results


class TransferPayload(TypedDict):
    """A dictionary structure for carrying transfer information."""

    custom_id: str
    source_track_id: int


def _to_numpy(data: Union[Tensor, NDArray[Any]]) -> NDArray[Any]:
    """
    Converts a PyTorch Tensor to a NumPy array. If the input is already a
    NumPy array, it is returned without change. This is a type-safe operation.
    """
    if isinstance(data, Tensor):
        return cast(NDArray[Any], data.cpu().numpy())
    return data


def generate_unique_id(length: int = 4) -> str:
    """Generates a unique alphanumeric ID for a vehicle."""
    return "CAR-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )


@dataclass
class VehicleTracker:
    """Manages the state and logic for tracking vehicles and transferring IDs."""

    polygons: Dict[str, Polygon]
    total_vehicle_count: int = 0
    counted_track_ids: Set[int] = field(default_factory=set)
    track_to_custom_id: Dict[int, str] = field(default_factory=dict)

    def update(self, yolo_results: List[Results]) -> None:
        """Processes YOLO results to update vehicle counts and handle ID transfers."""
        if yolo_results[0].boxes is None or yolo_results[0].boxes.id is None:
            return

        boxes_np = _to_numpy(yolo_results[0].boxes.xyxy)
        track_ids_np = _to_numpy(yolo_results[0].boxes.id)

        payload_left = self._check_triggers(
            boxes_np,
            track_ids_np,
            "zone_trigger_left_lane",
        )
        payload_right = self._check_triggers(
            boxes_np,
            track_ids_np,
            "zone_trigger_right_lane",
        )

        self._execute_transfers(
            boxes_np,
            track_ids_np,
            payload_left,
            "zone_destination_left_lane",
        )
        self._execute_transfers(
            boxes_np,
            track_ids_np,
            payload_right,
            "zone_destination_right_lane",
        )

    def _check_triggers(
        self,
        boxes: NDArray[np.float32],
        track_ids: NDArray[np.int_],
        trigger_zone_name: str,
    ) -> TransferPayload | None:
        payload: TransferPayload | None = None
        for box, track_id in zip(boxes, track_ids, strict=False):
            track_id = int(track_id)

            center_point = Point((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
            if (
                self.polygons["zone_a_counting"].contains(center_point)
                and track_id not in self.counted_track_ids
            ):
                self.total_vehicle_count += 1
                self.counted_track_ids.add(track_id)
                if track_id not in self.track_to_custom_id:
                    self.track_to_custom_id[track_id] = generate_unique_id()

            if (
                self.polygons[trigger_zone_name].contains(center_point)
                and track_id in self.track_to_custom_id
            ):
                payload = TransferPayload(
                    custom_id=self.track_to_custom_id[track_id],
                    source_track_id=track_id,
                )
                break
        return payload

    def _execute_transfers(
        self,
        boxes: NDArray[np.float32],
        track_ids: NDArray[np.int_],
        payload: TransferPayload | None,
        dest_zone_name: str,
    ) -> None:
        if not payload:
            return
        for box, track_id in zip(boxes, track_ids, strict=False):
            track_id = int(track_id)

            center_point = Point((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
            if (
                self.polygons[dest_zone_name].contains(center_point)
                and track_id != payload["source_track_id"]
            ):
                self.track_to_custom_id[track_id] = payload["custom_id"]
