from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from yapml.db import engine, get_session
from yapml.fixtures import populate_db

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


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
