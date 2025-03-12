import fasthtml.common as fh

from datamodel import ImageDetectionSample


def image_card(sample: ImageDetectionSample, width: int = 200, height: int = 200):
    boxes = sample.boxes
    image_url = sample.image_url

    # Parent container for image and boxes
    parent_div = fh.Div(style="position: relative; display: inline-block;")  # This is crucial!

    img = fh.Img(src=f"{image_url}", style=f"width: {width}px; height: {height}px;")

    # Overlay boxes
    box_divs = []
    for box in boxes:
        # Convert normalized coordinates to pixels
        x = box.center_x * width
        y = box.center_y * height
        w = box.width * width
        h = box.height * height

        # Calculate box corners
        left = x - w / 2
        top = y - h / 2

        # Box div with absolute positioning (relative to parent)
        box_divs.append(
            fh.Div(
                style=f"""
            position: absolute;
            left: {left}px;
            top: {top}px;
            width: {w}px;
            height: {h}px;
            border: 2px solid red;
            box-sizing: border-box;
            pointer-events: none;
            """
            )
        )

    return parent_div(img, *box_divs)


def image_list(samples: list[ImageDetectionSample]):
    return fh.Div(*[image_card(sample) for sample in samples])
