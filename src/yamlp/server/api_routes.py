from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import select

from yamlp.datamodel import BoundingBox, ObjectDetectionSample
from yamlp.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


@router.get("/samples")
async def get_samples(request: Request) -> list[ObjectDetectionSample]:
    session = request.state.session

    query = select(ObjectDetectionSample).options(selectinload(ObjectDetectionSample.boxes))
    results = session.exec(query).all()
    return results


@router.get("/samples/{sample_id}")
async def get_sample(request: Request, sample_id: int) -> ObjectDetectionSample:
    session = request.state.session
    sample = session.get(ObjectDetectionSample, sample_id)
    return sample


# Define the update schema
class BoxUpdate(BaseModel):
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    label_name: Optional[str] = None
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
        label_name=update_data.label_name if update_data.label_name else box.label_name,
        annotator_name=update_data.annotator_name if update_data.annotator_name else box.annotator_name,
    )
    session.add(new_box)
    session.commit()
    session.refresh(new_box)
    return new_box
