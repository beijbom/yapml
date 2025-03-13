import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine

from yamlp.config import sqlite_url
from yamlp.fixtures import populate_db
from yamlp.server.api_routes import router as api_router
from yamlp.server.ui_routes import router as ui_router

web_app = FastAPI()


@web_app.get("/reset_db", response_class=HTMLResponse)
async def reset_db() -> HTMLResponse:
    web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")
    os.makedirs("/data/images", exist_ok=True)
    Path("/data/database.db").unlink(missing_ok=True)
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)
    populate_db()
    return "<h1>Database was reset.</h1>"


web_app.include_router(api_router)
web_app.include_router(ui_router)
