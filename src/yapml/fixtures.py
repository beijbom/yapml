from datetime import datetime, timedelta
from io import BytesIO

import requests
from PIL import Image as PILImage
from sqlmodel import Session, create_engine

from yapml.config import image_dir, image_url_prefix, sqlite_url
from yapml.datamodel import BoundingBox, FunctionType, Label, ObjectDetectionSample, YapFunction


def populate_db() -> None:
    # Get a random image from Lorem Picsum
    response = requests.get("https://picsum.photos/500/500")
    pil_image = PILImage.open(BytesIO(response.content))
    pil_image.save(f"{image_dir}/test1.jpg")

    response = requests.get("https://picsum.photos/500/500")
    pil_image = PILImage.open(BytesIO(response.content))
    pil_image.save(f"{image_dir}/test2.jpg")

    engine = create_engine(sqlite_url)

    with Session(engine) as session:
        function = YapFunction(
            name="Test fixture", description="Object Detection", function_type=FunctionType.OBJECT_DETECTION
        )
        session.add(function)
        session.commit()
        assert function.id is not None

        # First transaction: Add images
        sample1 = ObjectDetectionSample(
            key="test1.jpg", width=500, height=500, url=f"{image_url_prefix}/test1.jpg", function_id=function.id
        )
        sample2 = ObjectDetectionSample(
            key="test2.jpg", width=500, height=500, url=f"{image_url_prefix}/test2.jpg", function_id=function.id
        )
        session.add_all([sample1, sample2])
        session.commit()

        label1 = Label(name="dog", color="#00A020", function_id=function.id)
        label2 = Label(name="cat", color="#FF0000", function_id=function.id)
        session.add_all([label1, label2])
        session.commit()

        # Create and add boxes in the same session after images are committed
        assert sample1.id is not None
        assert sample2.id is not None
        assert label1.id is not None
        assert label2.id is not None
        box1 = BoundingBox(
            center_x=0.1,
            center_y=0.1,
            width=0.1,
            height=0.1,
            label_id=label1.id,
            sample_id=sample1.id,
            annotator_name="alice",
            function_id=function.id,
        )
        box2 = BoundingBox(
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            label_id=label2.id,
            sample_id=sample1.id,
            annotator_name="bob",
            function_id=function.id,
        )
        box3 = BoundingBox(
            center_x=0.8,
            center_y=0.8,
            width=0.1,
            height=0.1,
            label_id=label1.id,
            sample_id=sample2.id,
            annotator_name="alice",
            function_id=function.id,
            created_at=datetime.now() - timedelta(days=10),
        )

        session.add_all([box1, box2, box3])
        session.commit()
        box4 = BoundingBox(
            center_x=0.8,
            center_y=0.8,
            width=0.2,
            height=0.1,
            label_id=label1.id,
            sample_id=sample2.id,
            annotator_name="alice",
            previous_box_id=box3.id,
            function_id=function.id,
        )
        session.add(box4)
        session.commit()
