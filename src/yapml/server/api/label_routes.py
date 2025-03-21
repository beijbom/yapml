from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import AfterValidator, BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from yapml.datamodel import Label, is_valid_hex_color, is_valid_label_name
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


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
    return label


@router.get("/labels")
async def list_labels(request: Request) -> list[Label]:
    session = request.state.session
    query = select(Label)
    results = session.exec(query).all()
    return results


@router.post("/labels", response_model=Label)
async def create_label_json(request: Request, label_data: Label) -> Label:
    session = request.state.session

    # Check if label with this name already exists
    existing = session.exec(select(Label).where(Label.name == label_data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label with this name already exists")

    # Create new label
    label = Label(name=label_data.name, color=label_data.color)
    validate_label(label)

    session.add(label)
    session.commit()
    session.refresh(label)
    return label


# This is used for the form submission from the labels page.
@router.post("/labels-form", include_in_schema=False)
async def create_label_form(request: Request, name: str = Form(...), color: str = Form(...)) -> RedirectResponse:
    label = Label(name=name, color=color)
    validate_label(label)

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
