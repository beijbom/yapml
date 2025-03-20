from fastapi import APIRouter, Depends, Request
from sqlmodel import select

from yapml.datamodel import ObjectDetectionSample
from yapml.db import get_session

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


@router.get("/samples")
async def list_samples(request: Request) -> list[ObjectDetectionSample]:
    session = request.state.session

    query = select(ObjectDetectionSample)
    results = session.exec(query).all()
    for sample in results:
        _ = sample.boxes
    return results


@router.get("/samples/{sample_id}")
async def get_sample(request: Request, sample_id: int) -> ObjectDetectionSample:
    session = request.state.session
    sample = session.get(ObjectDetectionSample, sample_id)
    return sample
