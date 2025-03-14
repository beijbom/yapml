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
    page = client.render_sample_list_page(samples)
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples")
async def samples_list_page(request: Request) -> HTMLResponse:
    samples = await get_samples(request)
    page = client.render_sample_list_page(samples)
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples/{image_id}")
async def sample_page(request: Request, image_id: int) -> HTMLResponse:
    sample = await get_sample(request, image_id)

    # Check if this is an HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        print("HTMX request")
        # For HTMX requests, just return the grid content
        grid_content = fh.Div(
            {"class": "grid", "id": "content-grid"},
            client.render_image_card(sample),
            client.render_sample_history(list(sample.boxes)),
        )
        return HTMLResponse(fh.to_xml(grid_content))

    else:
        print("Full page request")
        page = client.render_sample_page(sample)
        return HTMLResponse(fh.to_xml(page))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(favicon_path)
