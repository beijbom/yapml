# Define the update schema
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


class BoxUpdate(BaseModel):
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    annotator_name: Optional[str] = None


@router.put("/boxes/{box_id}")
def update_box(request: Request, box_id: int, update_data: BoxUpdate) -> BoundingBox:
    session = request.state.session
    box = session.get(BoundingBox, box_id)
    print(f"Got box: {box}")
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    new_box = BoundingBox(
        sample_id=box.sample_id,
        previous_box_id=box.id,
        center_x=update_data.center_x if update_data.center_x else box.center_x,
        center_y=update_data.center_y if update_data.center_y else box.center_y,
        width=update_data.width if update_data.width else box.width,
        height=update_data.height if update_data.height else box.height,
        label_id=box.label.id,
        annotator_name=update_data.annotator_name if update_data.annotator_name else box.annotator_name,
    )
    session.add(new_box)
    session.commit()
    session.refresh(new_box)
    return new_box


class BoxCreate(BaseModel):
    sample_id: int
    label_id: int
    center_x: float
    center_y: float
    width: float
    height: float
    annotator_name: str = "A User"  # Default value if not provided


@router.post("/boxes", response_model=BoundingBox)
async def create_box(request: Request, box_data: BoxCreate) -> BoundingBox:
    session = request.state.session

    # Verify sample and label exist
    sample = session.get(ObjectDetectionSample, box_data.sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    label = session.get(Label, box_data.label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Create new box
    box = BoundingBox(
        sample_id=box_data.sample_id,
        label_id=box_data.label_id,
        center_x=box_data.center_x,
        center_y=box_data.center_y,
        width=box_data.width,
        height=box_data.height,
        annotator_name=box_data.annotator_name,
    )
    session.add(box)
    session.commit()
    session.refresh(box)
    return box
