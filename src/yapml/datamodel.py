import re
from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional

from pydantic import AfterValidator, BaseModel
from sqlmodel import Field, Relationship, SQLModel
from typing_extensions import Annotated


class FunctionType(Enum):
    OBJECT_DETECTION = "object_detection"


class YapFunction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    function_type: FunctionType
    labels: list["Label"] = Relationship(
        back_populates="function", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    samples: list["ObjectDetectionSample"] = Relationship(
        back_populates="function", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    boxes: list["BoundingBox"] = Relationship(
        back_populates="function", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


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
    function_id: int = Field(foreign_key="yapfunction.id")
    name: Annotated[str, AfterValidator(is_valid_label_name)] = Field(unique=True)
    color: Annotated[str, AfterValidator(is_valid_hex_color)] = Field()
    boxes: list["BoundingBox"] = Relationship(
        back_populates="label",
        sa_relationship_kwargs={
            "primaryjoin": "and_(Label.id == BoundingBox.label_id, BoundingBox.deleted_at.is_(None))",
        },
    )
    function: "YapFunction" = Relationship(back_populates="labels")
    deleted_at: Optional[datetime] = Field(default=None)


def is_valid_box_center_range(v: float) -> float:
    if v < 0 or v > 1.0:
        raise ValueError("Center must be between 0 and 1.0")
    return v


def is_valid_box_size_range(v: float) -> float:
    if v <= 0 or v > 1.0:
        raise ValueError("Dimension must be greater than 0 and less than or equal to 1.0")
    return v


class BoundingBox(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sample_id: int = Field(foreign_key="objectdetectionsample.id")
    function_id: int = Field(foreign_key="yapfunction.id")
    label_id: int = Field(foreign_key="label.id")
    center_x: Annotated[float, AfterValidator(is_valid_box_center_range)]
    center_y: Annotated[float, AfterValidator(is_valid_box_center_range)]
    width: Annotated[float, AfterValidator(is_valid_box_size_range)]
    height: Annotated[float, AfterValidator(is_valid_box_size_range)]
    annotator_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field(default=None)
    previous_box_id: Optional[int] = Field(default=None, foreign_key="boundingbox.id", unique=True)
    sample: "ObjectDetectionSample" = Relationship(back_populates="boxes")
    label: Label = Relationship(back_populates="boxes")
    function: "YapFunction" = Relationship(back_populates="boxes")


class BoxChange(BaseModel):
    label_name: str
    annotator_name: str
    event: str
    time_delta: str


def suppress_stale_boxes(boxes: list[BoundingBox]) -> list[BoundingBox]:
    stale_box_ides = set([box.previous_box_id for box in boxes if box.previous_box_id is not None])
    return [box for box in boxes if box.id not in stale_box_ides]


def is_valid_height_width(v: int) -> int:
    if v <= 0:
        raise ValueError("Height and width must be greater than 0")
    return v


class ObjectDetectionSample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    function_id: int = Field(foreign_key="yapfunction.id")
    url: str
    key: Optional[str] = Field(default=None)  # Optional key for the sample
    image_hash: Optional[str] = Field(default=None, index=True, unique=True)  # Optional hash for the sample
    width: Optional[Annotated[int, AfterValidator(is_valid_height_width)]] = Field(default=None)
    height: Optional[Annotated[int, AfterValidator(is_valid_height_width)]] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field(default=None)
    boxes: list[BoundingBox] = Relationship(
        back_populates="sample",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BoundingBox.sample_id == ObjectDetectionSample.id, BoundingBox.deleted_at.is_(None))",
        },
    )
    function: "YapFunction" = Relationship(back_populates="samples")
