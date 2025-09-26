import json

from loguru import logger
from shapely.geometry import Point


class CounterManager:
    """
    Manages the counting of vehicles based on their class and tracks their IDs.
    """

    def __init__(self):
        self.counted_track_ids = set()

        self.class_id_to_name = {2: "car", 5: "bus", 7: "truck"}

        self.counts = {"car": 0, "bus": 0, "truck": 0, "total": 0}
        logger.info("CounterManager initialized.")

    def update(self, tracked_objects, green_zone_polygon):
        """
        Updates the counts based on objects entering the green zone.

        Args:
            tracked_objects (list): A list of tensors, where each tensor
                                    contains [x1, y1, x2, y2, track_id, conf, cls].
            green_zone_polygon (Shapely Polygon): The polygon for the counting area.
        """
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id, conf, cls = obj

            # Convert tensor values to standard Python types for processing
            track_id = int(track_id)
            class_id = int(cls)

            # Calculate the center point of the bounding box
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            center_point = Point(center_x, center_y)

            if (
                green_zone_polygon.contains(center_point)
                and track_id not in self.counted_track_ids
            ):
                self.counted_track_ids.add(track_id)
                vehicle_type = self.class_id_to_name.get(class_id)

                if vehicle_type:
                    self.counts[vehicle_type] += 1
                    self.counts["total"] += 1
                    logger.debug(
                        f"Counted new {vehicle_type} with ID {track_id}."
                        f" Total count: {self.counts['total']}"
                    )

    def get_current_counts(self):
        """Returns the current dictionary of counts."""
        return self.counts

    def save_statistics(self, filepath="statistics.json"):
        """Saves the final counts to a JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.counts, f, indent=4)
            logger.info(f"Successfully saved counting statistics to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save statistics to {filepath}. Error: {e}")
