from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import AfterValidator, BaseModel
from sqlmodel import SQLModel, select

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample, is_valid_hex_color, is_valid_label_name
from yapml.db import engine, get_session
from yapml.fixtures import populate_db

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


@router.get("/samples")
async def list_samples(request: Request) -> list[ObjectDetectionSample]:
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
async def list_labels(request: Request) -> list[Label]:
    session = request.state.session
    query = select(Label)
    results = session.exec(query).all()
    return results


@router.post("/labels", response_model=Label)
async def create_label_json(
    request: Request,
    label_data: Annotated[Label, AfterValidator(Label.model_validate)],
) -> Label:
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
@router.post("/labels-form", include_in_schema=False)
async def create_label_form(request: Request, name: str = Form(...), color: str = Form(...)) -> RedirectResponse:
    try:
        is_valid_label_name(name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        is_valid_hex_color(color)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    label = Label(name=name, color=color)
    session = request.state.session
    session.add(label)
    session.commit()
    return RedirectResponse(url="/labels", status_code=303)


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


@router.put("/labels/{label_id}")
async def update_label(request: Request, label_id: int, update_data: LabelUpdate) -> Label:

    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    if update_data.color is not None:
        try:
            is_valid_hex_color(update_data.color)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        label.color = update_data.color

    if update_data.name is not None:
        try:
            is_valid_label_name(update_data.name)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        existing = session.exec(select(Label).where(Label.name == update_data.name)).first()
        if existing and existing.id != label_id:
            raise HTTPException(status_code=400, detail="Label with this name already exists")
        label.name = update_data.name

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

    # Return empty response with 204 No Content status
    return Response(status_code=204)


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


@router.post("/reset-db")
async def reset_db() -> JSONResponse:
    try:
        # Drop all tables
        SQLModel.metadata.drop_all(engine)

        # Create new tables
        SQLModel.metadata.create_all(engine)
        populate_db()

        return JSONResponse({"status": "success", "message": "Database was reset successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
