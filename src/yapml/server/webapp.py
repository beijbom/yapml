import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from yapml.db import engine
from yapml.fixtures import populate_db
from yapml.server.api import admin_router, boundingbox_router, label_router, sample_router
from yapml.server.ui_routes import router as ui_router

web_app = FastAPI()

os.makedirs("/data/images", exist_ok=True)
web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")

web_app.include_router(admin_router)
web_app.include_router(boundingbox_router)
web_app.include_router(label_router)
web_app.include_router(sample_router)
web_app.include_router(ui_router)
