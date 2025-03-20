import re
from datetime import datetime
from typing import Optional

from pydantic import AfterValidator
from sqlmodel import Field, Relationship, SQLModel
from typing_extensions import Annotated


def is_valid_hex_color(v: str) -> str:
    if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
        raise ValueError("Invalid hex color format. Must be #RRGGBB")
    return v


def is_valid_label_name(v: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]+$", v):
        raise ValueError("Name must contain only alphanumeric characters and underscores")
    return v


class Label(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Annotated[str, AfterValidator(is_valid_label_name)] = Field(unique=True)
    color: Annotated[str, AfterValidator(is_valid_hex_color)] = Field(unique=True)
    boxes: list["BoundingBox"] = Relationship(
        back_populates="label", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class BoundingBox(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    center_x: float
    center_y: float
    width: float
    height: float
    label_id: int = Field(foreign_key="label.id")
    annotator_name: str
    sample_id: int = Field(foreign_key="objectdetectionsample.id")
    created_at: datetime = Field(default_factory=datetime.now)
    previous_box_id: Optional[int] = Field(default=None, foreign_key="boundingbox.id", unique=True)
    sample: "ObjectDetectionSample" = Relationship(back_populates="boxes")
    label: Label = Relationship(back_populates="boxes")


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
