from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import select

from yamlp.datamodel import BoundingBox, Label, ObjectDetectionSample
from yamlp.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


@router.get("/samples")
async def get_samples(request: Request) -> list[ObjectDetectionSample]:
    session = request.state.session

    query = select(ObjectDetectionSample)
    results = session.exec(query).all()
    for sample in results:
        _ = sample.boxes
    return results


@router.get("/samples/{sample_id}")
async def get_sample(request: Request, sample_id: int) -> ObjectDetectionSample:
    session = request.state.session
    sample = session.get(ObjectDetectionSample, sample_id)
    return sample


@router.get("/labels")
async def get_labels(request: Request) -> list[Label]:
    session = request.state.session
    query = select(Label)
    results = session.exec(query).all()
    return results


class LabelUpdate(BaseModel):
    color: str


@router.put("/labels/{label_id}")
async def update_label(request: Request, label_id: int, update_data: LabelUpdate) -> Label:
    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Update the label color
    label.color = update_data.color
    session.add(label)
    session.commit()
    session.refresh(label)
    return label


@router.delete("/labels/{label_id}")
async def delete_label(request: Request, label_id: int):
    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Delete the label
    session.delete(label)
    session.commit()
    return {"message": "Label deleted successfully"}


# Define the update schema
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


class LabelCreate(BaseModel):
    name: str
    color: str


@router.post("/labels", response_model=Label)
async def create_label_json(request: Request, label_data: LabelCreate) -> Label:
    session = request.state.session

    # Check if label with this name already exists
    existing = session.exec(select(Label).where(Label.name == label_data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label with this name already exists")

    # Create new label
    label = Label(name=label_data.name, color=label_data.color)
    session.add(label)
    session.commit()
    session.refresh(label)
    return label


# This is used for the form submission from the labels page.
@router.post("/labels", include_in_schema=False)
async def create_label_form(request: Request, name: str = Form(...), color: str = Form(...)):
    session = request.state.session

    # Check if label with this name already exists
    existing = session.exec(select(Label).where(Label.name == name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label with this name already exists")

    # Create new label
    label = Label(name=name, color=color)
    session.add(label)
    session.commit()

    # Redirect back to the labels page
    return RedirectResponse(url="/labels", status_code=303)
