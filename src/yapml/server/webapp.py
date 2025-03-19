import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine
from yapml.config import sqlite_file_name, sqlite_url
from yapml.fixtures import populate_db
from yapml.server.api_routes import router as api_router
from yapml.server.ui_routes import router as ui_router

web_app = FastAPI()


@web_app.get("/reset_db", response_class=HTMLResponse)
async def reset_db() -> HTMLResponse:
    # First ensure the directory exists
    os.makedirs("/data/images", exist_ok=True)

    # Remove old database if it exists
    if os.path.exists(sqlite_file_name):
        os.remove(sqlite_file_name)

    # Create new database and populate it
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)
    populate_db()

    return HTMLResponse("<h1>Database was reset.</h1>")


# This should be at app initialization, not in the reset_db function
os.makedirs("/data/images", exist_ok=True)
web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")

web_app.include_router(api_router)
web_app.include_router(ui_router)
