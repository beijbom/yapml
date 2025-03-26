from datetime import datetime

from yapml.client.utils import time_delta_string
from yapml.datamodel import BoundingBox, BoxChange


def boxes_to_changes(boxes: list[BoundingBox]) -> list[BoxChange]:
    if not boxes:
        return []
    box_by_id = {box.id: box for box in boxes}
    box_ids_not_yet_seen = [box.id for box in boxes]

    box = box_by_id[box_ids_not_yet_seen[-1]]
    changes: list[BoxChange] = []
    now = datetime.now()
    while box_ids_not_yet_seen:
        box_ids_not_yet_seen.remove(box.id)
        if box.deleted_at:
            changes.append(
                BoxChange(
                    label_name=box.label.name,
                    annotator_name=box.annotator_name,
                    event="deleted",
                    time_delta=time_delta_string(now - box.deleted_at),
                )
            )
        if not box.previous_box_id:
            changes.append(
                BoxChange(
                    label_name=box.label.name,
                    annotator_name=box.annotator_name,
                    event="created",
                    time_delta=time_delta_string(now - box.created_at),
                )
            )
            if box_ids_not_yet_seen:
                box = box_by_id[box_ids_not_yet_seen[-1]]
        else:
            previous_box = box_by_id[box.previous_box_id]
            if previous_box.width != box.width or previous_box.height != box.height:
                changes.append(
                    BoxChange(
                        label_name=box.label.name,
                        annotator_name=box.annotator_name,
                        event="resized",
                        time_delta=time_delta_string(now - box.created_at),
                    )
                )
            elif previous_box.center_x != box.center_x or previous_box.center_y != box.center_y:
                changes.append(
                    BoxChange(
                        label_name=box.label.name,
                        annotator_name=box.annotator_name,
                        event="moved",
                        time_delta=time_delta_string(now - box.created_at),
                    )
                )
            box = previous_box
    return changes
