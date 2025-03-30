# Define the update schema
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastlite import ver2tuple
from pydantic import AfterValidator, BaseModel, ValidationError
from sqlmodel import select

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample
from yapml.db import get_session

router = APIRouter(prefix="/api/detection", dependencies=[Depends(get_session)], tags=["Object Detection Boxes"])


def validate_box(box: BoundingBox) -> BoundingBox:
    try:
        BoundingBox.model_validate(box)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return box


@router.get("/boxes/{box_id}")
async def get_box(request: Request, box_id: int) -> BoundingBox:
    session = request.state.session
    box = session.get(BoundingBox, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    return box


@router.get("/boxes")
async def list_boxes(
    request: Request,
    include_deleted: bool = False,
    sample_id: Optional[int] = None,
    function_id: Optional[int] = None,
) -> list[BoundingBox]:
    session = request.state.session
    boxes = session.exec(
        select(BoundingBox)
        .where(BoundingBox.deleted_at.is_(None) if not include_deleted else True)  # type: ignore
        .where(BoundingBox.sample_id == sample_id if sample_id else True)
        .where(BoundingBox.sample.function_id == function_id if function_id else True)
    ).all()
    return boxes


@router.post("/boxes", response_model=BoundingBox)
async def create_box(request: Request, box: BoundingBox) -> BoundingBox:
    session = request.state.session

    # Verify sample and label exist
    sample = session.get(ObjectDetectionSample, box.sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    label = session.get(Label, box.label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Create new box
    _ = validate_box(box)
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
        function_id=box.function_id,
        previous_box_id=box.id,
        label_id=box.label.id,
        center_x=update_data.center_x if update_data.center_x else box.center_x,
        center_y=update_data.center_y if update_data.center_y else box.center_y,
        width=update_data.width if update_data.width else box.width,
        height=update_data.height if update_data.height else box.height,
        annotator_name=update_data.annotator_name if update_data.annotator_name else box.annotator_name,
    )
    _ = validate_box(new_box)
    session.add_all([new_box, box])
    session.commit()
    session.refresh(new_box)
    return new_box


@router.delete("/boxes/{box_id}")
async def delete_box(request: Request, box_id: int) -> Response:
    session = request.state.session
    box = session.get(BoundingBox, box_id)
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    box.deleted_at = datetime.now()
    session.add(box)
    session.commit()
    return Response(status_code=204)
