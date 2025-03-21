# Define the update schema
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import AfterValidator, BaseModel, ValidationError
from sqlmodel import select

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


@router.get("/boxes/{box_id}")
async def get_box(request: Request, box_id: int) -> BoundingBox:
    session = request.state.session
    box = session.get(BoundingBox, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.get("/boxes")
async def list_boxes(request: Request) -> list[BoundingBox]:
    session = request.state.session
    boxes = session.exec(select(BoundingBox)).all()
    return boxes


@router.post("/boxes", response_model=BoundingBox)
async def create_box(
    request: Request, box_data: Annotated[BoundingBox, AfterValidator(BoundingBox.model_validate)]
) -> BoundingBox:
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
    try:
        BoundingBox.model_validate(new_box)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    session.add(new_box)
    session.commit()
    session.refresh(new_box)
    return new_box


@router.delete("/boxes/{box_id}")
async def delete_box(request: Request, box_id: int):
    session = request.state.session
    box = session.get(BoundingBox, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    session.delete(box)
    session.commit()
    return Response(status_code=204)
