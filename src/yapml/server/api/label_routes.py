from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError
from sqlmodel import select

from yapml.datamodel import BoundingBox, Label
from yapml.db import get_session

router = APIRouter(prefix="/api/detection", dependencies=[Depends(get_session)], tags=["Object Detection Labels"])


def validate_label(label: Label) -> Label:
    try:
        Label.model_validate(label)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return label


@router.get("/labels/{label_id}")
async def get_label(request: Request, label_id: int) -> Label:
    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return label


@router.get("/labels")
async def list_labels(request: Request, function_id: int | None = None) -> list[Label]:
    session = request.state.session
    query = select(Label).where(Label.deleted_at.is_(None))  # type: ignore
    if function_id is not None:
        query = query.where(Label.function_id == function_id)
    results = session.exec(query).all()
    return results


@router.post("/labels", response_model=Label)
async def create_label_json(request: Request, label: Label) -> Label:
    session = request.state.session

    # Check if label with this name already exists
    existing = session.exec(select(Label).where(Label.name == label.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label with this name already exists")

    _ = validate_label(label)

    session.add(label)
    session.commit()
    session.refresh(label)
    return label


# This is used for the form submission from the labels page.
@router.post("/labels-form", include_in_schema=False)
async def create_label_form(
    request: Request, name: str = Form(...), color: str = Form(...), function_id: int = Form(...)
) -> RedirectResponse:
    label = Label(name=name, color=color, function_id=function_id)
    validate_label(label)

    session = request.state.session
    session.add(label)
    session.commit()
    return RedirectResponse(url=f"/functions/{function_id}/labels", status_code=303)


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


@router.put("/labels/{label_id}")
async def update_label(request: Request, label_id: int, update_data: LabelUpdate) -> Label:
    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Check if the name is being changed to a name that already exists
    if update_data.name is not None:
        existing = session.exec(select(Label).where(Label.name == update_data.name)).first()
        if existing and existing.id != label_id:
            raise HTTPException(status_code=400, detail="Label with this name already exists")

    label.color = update_data.color if update_data.color else label.color
    label.name = update_data.name if update_data.name else label.name
    validate_label(label)

    session.add(label)
    session.commit()
    session.refresh(label)

    return label


@router.delete("/labels/{label_id}")
async def delete_label(request: Request, label_id: int) -> Response:
    session = request.state.session
    label = session.get(Label, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # Check if the label is used by any boxes
    boxes = session.exec(select(BoundingBox).where(BoundingBox.label_id == label_id)).all()
    for box in boxes:
        box.deleted_at = datetime.now()
        session.add(box)

    label.deleted_at = datetime.now()
    session.add(label)
    session.commit()

    # Return empty response with 204 No Content status
    return Response(status_code=204)
