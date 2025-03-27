from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError
from sqlmodel import select

from yapml.datamodel import FunctionType, YapFunction
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


def validate_function(function: YapFunction) -> YapFunction:
    try:
        YapFunction.model_validate(function)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return function


@router.get("/functions/{function_id}")
async def get_function(request: Request, function_id: int) -> YapFunction:
    session = request.state.session
    function = session.get(YapFunction, function_id)
    if not function:
        raise HTTPException(status_code=404, detail="Function not found")
    return function


@router.get("/functions")
async def list_functions(request: Request) -> list[YapFunction]:
    session = request.state.session
    query = select(YapFunction)
    results = session.exec(query).all()
    return results


@router.post("/functions", response_model=YapFunction)
async def create_function(request: Request, function: YapFunction) -> YapFunction:
    session = request.state.session

    # Check if function with this name already exists
    existing = session.exec(select(YapFunction).where(YapFunction.name == function.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Function with this name already exists")

    validate_function(function)

    session.add(function)
    session.commit()
    session.refresh(function)
    return function


@router.post("/functions-form", include_in_schema=False)
async def create_function_form(
    request: Request, name: str = Form(...), description: str = Form(...)
) -> RedirectResponse:
    function = YapFunction(name=name, description=description, function_type=FunctionType.OBJECT_DETECTION)
    validate_function(function)

    session = request.state.session
    session.add(function)
    session.commit()
    return RedirectResponse(url=f"/functions/{function.id}/samples", status_code=303)


class FunctionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.put("/functions/{function_id}")
async def update_function(request: Request, function_id: int, update_data: FunctionUpdate) -> YapFunction:
    session = request.state.session
    function = session.get(YapFunction, function_id)
    if not function:
        raise HTTPException(status_code=404, detail="Function not found")

    # Check if the name is being changed to a name that already exists
    if update_data.name is not None:
        existing = session.exec(select(YapFunction).where(YapFunction.name == update_data.name)).first()
        if existing and existing.id != function_id:
            raise HTTPException(status_code=400, detail="Function with this name already exists")

    # Update fields if provided
    if update_data.name is not None:
        function.name = update_data.name
    if update_data.description is not None:
        function.description = update_data.description

    validate_function(function)

    session.add(function)
    session.commit()
    session.refresh(function)
    return function


@router.delete("/functions/{function_id}")
async def delete_function(request: Request, function_id: int) -> Response:
    session = request.state.session
    function = session.get(YapFunction, function_id)
    if not function:
        raise HTTPException(status_code=404, detail="Function not found")

    session.delete(function)
    session.commit()
    return Response(status_code=204)
