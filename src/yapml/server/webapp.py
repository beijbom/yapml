import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel
from yapml.db import engine
from yapml.fixtures import populate_db
from yapml.server.api_routes import router as api_router
from yapml.server.ui_routes import router as ui_router

web_app = FastAPI()


@web_app.post("/api/reset-db")
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


# This should be at app initialization, not in the reset_db function
os.makedirs("/data/images", exist_ok=True)
web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")

web_app.include_router(api_router)
web_app.include_router(ui_router)
