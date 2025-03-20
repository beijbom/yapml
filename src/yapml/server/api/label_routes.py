from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import AfterValidator, BaseModel
from sqlmodel import select

from yapml.datamodel import Label, is_valid_hex_color, is_valid_label_name
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


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
