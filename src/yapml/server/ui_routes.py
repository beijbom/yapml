import fasthtml.common as fh
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse

import yapml.client as client
from yapml.config import favicon_path
from yapml.db import get_session
from yapml.server.api import get_sample, list_boxes, list_labels, list_samples

router = APIRouter(prefix="", dependencies=[Depends(get_session)])


@router.get("/")
async def homepage(request: Request) -> HTMLResponse:
    samples = await list_samples(request)
    page = client.render_sample_list_page(samples)
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples")
async def samples_list_page(request: Request) -> HTMLResponse:
    samples = await list_samples(request)
    page = client.render_sample_list_page(samples)
    return HTMLResponse(fh.to_xml(page))


@router.get("/labels")
async def labels_page(request: Request) -> HTMLResponse:
    labels = await list_labels(request)
    page = client.render_label_list_page(labels)
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples/{image_id}")
async def sample_page(request: Request, image_id: int) -> HTMLResponse:
    sample = await get_sample(request, image_id)
    boxes = await list_boxes(request, sample_id=image_id, include_deleted=True)
    page = client.render_sample_details_page(sample, list(boxes))
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples/{sample_id}/history")
async def get_history(request: Request, sample_id: int) -> HTMLResponse:
    boxes = await list_boxes(request, sample_id=sample_id, include_deleted=True)
    return HTMLResponse(fh.to_xml(client.render_sample_history(list(boxes), sample_id)))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(favicon_path)


@router.get("/admin", response_class=HTMLResponse)
async def admin_page() -> HTMLResponse:
    return HTMLResponse(fh.to_xml(client.render_admin_page()))
