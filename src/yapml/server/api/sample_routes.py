import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from PIL import Image as PILImage
from pydantic import ValidationError
from sqlmodel import select

from yapml.config import image_dir, image_url_prefix
from yapml.datamodel import ObjectDetectionSample
from yapml.db import get_session
from yapml.image_processing import ImageDecoder

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])


def validate_sample(sample: ObjectDetectionSample) -> ObjectDetectionSample:
    try:
        ObjectDetectionSample.model_validate(sample)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return sample


@router.get("/samples/{sample_id}")
async def get_sample(request: Request, sample_id: int) -> ObjectDetectionSample:
    session = request.state.session
    sample = session.get(ObjectDetectionSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample


@router.get("/samples")
async def list_samples(request: Request, function_id: int | None = None) -> list[ObjectDetectionSample]:
    session = request.state.session

    query = select(ObjectDetectionSample)
    if function_id is not None:
        query = query.where(ObjectDetectionSample.function_id == function_id)
    results = session.exec(query).all()
    for sample in results:
        _ = sample.boxes
    return results


@router.post("/samples", response_model=ObjectDetectionSample)
async def create_sample(request: Request, sample: ObjectDetectionSample) -> ObjectDetectionSample:
    session = request.state.session

    # Step1: Fetch and decode the image.
    source_url = sample.url
    try:
        image_bytes = ImageDecoder().to_stream(source_url)
        image = PILImage.open(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    if sample.width is None:
        sample.width = image.width
    elif image.width != sample.width:
        raise HTTPException(status_code=422, detail="Given width does not match image width")
    if sample.height is None:
        sample.height = image.height
    elif image.height != sample.height:
        raise HTTPException(status_code=422, detail="Given height does not match image height")

    # Step2: Check if the image already exists in the database.
    image_hash = hashlib.md5(image.tobytes()).hexdigest()
    statement = select(ObjectDetectionSample).where(ObjectDetectionSample.image_hash == image_hash)
    result = session.exec(statement).first()
    if result:
        raise HTTPException(status_code=409, detail="Image already exists in database")

    # Step3: Update fields and save image to the database.
    sample.image_hash = image_hash
    sample.url = f"{image_url_prefix}/{image_hash}"
    validate_sample(sample)  # Validate the sample again to ensure all fields are valid

    # Write the bytes to disk. Note that there is no file extension.
    file_path = f"{image_dir}/{image_hash}"
    with open(file_path, "wb") as file:  # Open the file in binary write mode
        file.write(image_bytes.getbuffer())  # Write the byte stream to the file

    session.add(sample)
    session.commit()
    session.refresh(sample)
    return sample


@router.delete("/samples/{sample_id}")
async def delete_sample(request: Request, sample_id: int) -> Response:
    session = request.state.session
    sample = session.get(ObjectDetectionSample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    session.delete(sample)
    session.commit()
    return Response(status_code=204)
