import os
from pathlib import Path
from typing import Optional

import fasthtml.common as fh
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select

import yamlp.client as client
import yamlp.datamodel as datamodel
from yamlp.config import favicon_path, sqlite_url
from yamlp.fixtures import populate_db

engine = create_engine(sqlite_url, echo=True)


def get_session():

    with Session(engine) as session:
        yield session


web_app = FastAPI()
router = APIRouter(prefix="/api", dependencies=[Depends(get_session)])


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
    annotator_name: Optional[str] = None


@router.put("/boxes/{box_id}")
def update_box(box_id: int, update_data: BoxUpdate, session: Session = Depends(get_session)) -> datamodel.BoundingBox:
    print(f"Updating box {box_id} with {update_data}")
    print(f"Getting box {box_id} from {engine.url}")
    box = session.get(datamodel.BoundingBox, box_id)
    print(f"Got box: {box}")
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")

    new_box = datamodel.BoundingBox(
        image_id=box.image_id,
        previous_box_id=box.id,
        center_x=update_data.center_x if update_data.center_x else box.center_x,
        center_y=update_data.center_y if update_data.center_y else box.center_y,
        width=update_data.width if update_data.width else box.width,
        height=update_data.height if update_data.height else box.height,
        label_name=update_data.label_name if update_data.label_name else box.label_name,
        annotator_name=update_data.annotator_name if update_data.annotator_name else box.annotator_name,
    )
    session.add(new_box)
    session.commit()
    session.refresh(new_box)
    return new_box


@web_app.get("/api/samples")
async def get_samples() -> list[datamodel.ImageDetectionSample]:
    with Session(engine) as session:
        query = select(datamodel.Image).options(selectinload(datamodel.Image.boxes))
        results = session.exec(query).all()
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


web_app.include_router(router)
