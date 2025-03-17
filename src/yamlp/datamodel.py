from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class BoundingBox(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    center_x: float
    center_y: float
    width: float
    height: float
    label_name: str
    annotator_name: str
    sample_id: int = Field(foreign_key="objectdetectionsample.id")
    created_at: datetime = Field(default_factory=datetime.now)
    previous_box_id: Optional[int] = Field(default=None, foreign_key="boundingbox.id", unique=True)
    sample: "ObjectDetectionSample" = Relationship(back_populates="boxes")


class ObjectDetectionSample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    url: str
    width: int
    height: int
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field(default=None)
    boxes: list[BoundingBox] = Relationship(back_populates="sample")


def suppress_stale_boxes(boxes: list[BoundingBox]) -> list[BoundingBox]:
    stale_box_ides = set([box.previous_box_id for box in boxes if box.previous_box_id is not None])
    return [box for box in boxes if box.id not in stale_box_ides]
