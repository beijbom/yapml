import fasthtml.common as fh
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel import select

import yamlp.client as client
from yamlp.config import favicon_path
from yamlp.datamodel import BoundingBox
from yamlp.db import get_session
from yamlp.server.api_routes import get_sample, get_samples

router = APIRouter(prefix="", dependencies=[Depends(get_session)])


@router.get("/")
async def homepage(request: Request) -> HTMLResponse:
    samples = await get_samples(request)
    page = fh.Html(fh.Head(fh.Title("Yet Another ML Platform")), client.image_list(samples))
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples/{image_id}")
async def sample_page(request: Request, image_id: int) -> HTMLResponse:
    session = request.state.session
    query = select(BoundingBox).where(BoundingBox.image_id == image_id)
    boxes = session.exec(query).all()
    sample_history = client.sample_history(list(boxes))
    sample = await get_sample(request, image_id)
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
                fh.Div({"class": "grid"}, card, sample_history),
            )
        ),
    )

    return HTMLResponse(fh.to_xml(page))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(favicon_path)
