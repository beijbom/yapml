import os
from pathlib import Path
from typing import Optional

import fasthtml.common as fh
import modal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select

import client
import datamodel
from config import favicon_path, sqlite_url
from fixtures import populate_db

web_app = FastAPI()
app = modal.App(name="yamlp")
volume = modal.Volume.from_name("YAMLP", create_if_missing=True)


modal_image = (
    modal.Image.debian_slim()
    .apt_install(["libgl1-mesa-glx", "libglib2.0-0"])
    .pip_install_from_pyproject("pyproject.toml")
    .add_local_python_source("datamodel", "config", "fixtures", "client")
    .add_local_dir("static", remote_path="/static")
)

engine = create_engine(sqlite_url, echo=True)


@web_app.get("/")
async def homepage() -> HTMLResponse:
    samples = await get_samples()
    page = fh.Html(fh.Head(fh.Title("Yet Another ML Platform")), client.image_list(samples))
    return HTMLResponse(fh.to_xml(page))


@web_app.get("/api/samples/{image_id}")
async def get_sample(image_id: int) -> datamodel.ImageDetectionSample:
    with Session(engine) as session:
        image = session.exec(select(datamodel.Image).where(datamodel.Image.id == image_id)).one()
        boxes = session.exec(select(datamodel.BoundingBox).where(datamodel.BoundingBox.image_id == image_id)).all()
        return datamodel.ImageDetectionSample(
            image_url=f"/images/{image.filename}",
            image_width=image.width,
            image_height=image.height,
            boxes=datamodel.suppress_stale_boxes(list(boxes)),
        )


# Define the update schema
class BoxUpdate(BaseModel):
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    label_name: Optional[str] = None


@web_app.put("/api/boxes/{box_id}")
def update_box(box_id: int, update_data: BoxUpdate):
    with Session(engine) as session:
        box = session.get(datamodel.BoundingBox, box_id)
        if not box:
            raise HTTPException(status_code=404, detail="Box not found")

        # Update only provided fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(box, field, value)

        session.commit()
        return box


@web_app.get("/api/samples")
async def get_samples() -> list[datamodel.ImageDetectionSample]:
    with Session(engine) as session:
        query = select(datamodel.Image).options(selectinload(datamodel.Image.boxes))
        results = session.exec(query).all()
        print(results)
        image_detection_samples = [
            datamodel.ImageDetectionSample(
                image_url=f"/images/{image.filename}",
                image_width=image.width,
                image_height=image.height,
                boxes=datamodel.suppress_stale_boxes(list(image.boxes)),
            )
            for image in results
        ]

        return image_detection_samples


@web_app.get("/samples/{image_id}")
async def sample_page(image_id: int) -> HTMLResponse:
    with Session(engine) as session:
        query = select(datamodel.BoundingBox).where(datamodel.BoundingBox.image_id == image_id)
        boxes = session.exec(query).all()
    sample_history = client.sample_history(list(boxes))
    sample = await get_sample(image_id)
    card = client.image_card(sample, width=500, height=500)

    page = fh.Html(
        fh.Head(
            fh.Title("Sample image page"),
            fh.Link({"rel": "stylesheet", "href": "https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"}),
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Sample image page"),
                fh.Div({"class": "grid"}, fh.Div(card), fh.Div(sample_history)),
            )
        ),
    )

    return HTMLResponse(fh.to_xml(page))


@web_app.get("/update-box")
async def update_box_page() -> HTMLResponse:
    form = client.update_box_form()
    page = fh.Html(fh.Head(fh.Title("Update box page")), fh.Body(form))
    return HTMLResponse(fh.to_xml(page))


@web_app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(favicon_path)


@web_app.get("/reset_db", response_class=HTMLResponse)
async def reset_db() -> HTMLResponse:
    web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")
    os.makedirs("/data/images", exist_ok=True)
    Path("/data/database.db").unlink(missing_ok=True)
    engine = create_engine(sqlite_url)
    SQLModel.metadata.create_all(engine)
    populate_db()
    return "<h1>Database was reset.</h1>"


@app.function(image=modal_image, container_idle_timeout=60, volumes={"/data": volume})
@modal.asgi_app()
def index() -> FastAPI:
    web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")
    return web_app
