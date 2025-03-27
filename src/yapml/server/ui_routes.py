import fasthtml.common as fh
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse

import yapml.client as client
from yapml.config import favicon_path
from yapml.db import get_session
from yapml.server.api import get_sample, list_boxes, list_functions, list_labels, list_samples

router = APIRouter(prefix="", dependencies=[Depends(get_session)])


@router.get("/")
async def homepage(request: Request) -> HTMLResponse:
    functions = await list_functions(request)
    page = client.render_function_list_page(functions)
    return HTMLResponse(fh.to_xml(page))


@router.get("/functions")
async def functions_page(request: Request) -> HTMLResponse:
    functions = await list_functions(request)
    page = client.render_function_list_page(functions)
    return HTMLResponse(fh.to_xml(page))


@router.get("/functions/{function_id}/samples")
async def samples_list_page(request: Request, function_id: int) -> HTMLResponse:
    samples = await list_samples(request, function_id=function_id)
    page = client.render_sample_list_page(function_id, samples)
    return HTMLResponse(fh.to_xml(page))


@router.get("/functions/{function_id}/labels")
async def labels_page(request: Request, function_id: int) -> HTMLResponse:
    labels = await list_labels(request, function_id=function_id)
    page = client.render_label_list_page(function_id, labels)
    return HTMLResponse(fh.to_xml(page))


@router.get("/functions/{function_id}/samples/{sample_id}")
async def sample_page(request: Request, function_id: int, sample_id: int) -> HTMLResponse:
    sample = await get_sample(request, sample_id)
    boxes = await list_boxes(request, sample_id=sample_id, include_deleted=True)
    page = client.render_sample_details_page(function_id, sample, list(boxes))
    return HTMLResponse(fh.to_xml(page))


@router.get("/samples/{sample_id}/history")
async def get_history(request: Request, sample_id: int) -> HTMLResponse:
    boxes = await list_boxes(request, sample_id=sample_id, include_deleted=True)
    return HTMLResponse(fh.to_xml(client.render_sample_history(list(boxes), sample_id)))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(favicon_path)


@router.get("/functions/{function_id}/admin", response_class=HTMLResponse)
async def admin_page(request: Request, function_id: int) -> HTMLResponse:
    return HTMLResponse(fh.to_xml(client.render_admin_page(function_id)))
