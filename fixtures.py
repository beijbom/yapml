import os
from io import BytesIO

import requests
from PIL import Image as PILImage
from sqlmodel import Session, create_engine

from config import image_dir, sqlite_url
from datamodel import BoundingBox, Image


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
        # First transaction: Add images
        image1 = Image(filename="test1.jpg", width=500, height=500)
        image2 = Image(filename="test2.jpg", width=500, height=500)
        session.add_all([image1, image2])
        session.commit()

        # Create and add boxes in the same session after images are committed
        box1 = BoundingBox(
            center_x=0.1,
            center_y=0.1,
            width=0.1,
            height=0.1,
            label_name="dog",
            image_id=image1.id,
            annotator_name="alice",
        )
        box2 = BoundingBox(
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            label_name="dog",
            image_id=image1.id,
            annotator_name="bob",
        )
        box3 = BoundingBox(
            center_x=0.8,
            center_y=0.8,
            width=0.1,
            height=0.1,
            label_name="dog",
            image_id=image2.id,
            annotator_name="alice",
        )

        session.add_all([box1, box2, box3])
        session.commit()
