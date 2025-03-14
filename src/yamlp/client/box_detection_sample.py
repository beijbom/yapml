import fasthtml.common as fh

from yamlp.datamodel import BoundingBox, ImageDetectionSample

# Add JavaScript for drag functionality
DRAG_SCRIPT = """
console.log('Script loaded');
let isDragging = false;
let currentBox = null;
let startX, startY;
let originalLeft, originalTop;
let imageRect;

function initializeDraggable() {
    console.log('Initializing draggable');
    const image = document.querySelector('img');
    imageRect = image.getBoundingClientRect();
    
    const boxes = document.querySelectorAll('.draggable-box');
    console.log('Found boxes:', boxes.length);
    boxes.forEach(box => {
        box.style.cursor = 'move';
        box.addEventListener('mousedown', startDragging);
    });
}

function startDragging(e) {
    isDragging = true;
    currentBox = e.target;
    startX = e.clientX;
    startY = e.clientY;
    originalLeft = currentBox.offsetLeft;
    originalTop = currentBox.offsetTop;
    
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDragging);
    e.preventDefault();
}

function drag(e) {
    if (!isDragging) return;
    
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    
    const newLeft = originalLeft + dx;
    const newTop = originalTop + dy;
    
    currentBox.style.left = `${newLeft}px`;
    currentBox.style.top = `${newTop}px`;
}

async function stopDragging() {
    if (!isDragging) return;
    isDragging = false;
    
    const boxId = currentBox.dataset.boxId;
    const imageWidth = parseFloat(currentBox.dataset.imageWidth);
    const imageHeight = parseFloat(currentBox.dataset.imageHeight);
    const boxWidth = parseFloat(currentBox.dataset.width);
    const boxHeight = parseFloat(currentBox.dataset.height);
    
    // Calculate normalized coordinates
    const centerX = (currentBox.offsetLeft + currentBox.offsetWidth/2) / imageWidth;
    const centerY = (currentBox.offsetTop + currentBox.offsetHeight/2) / imageHeight;
    
    try {
        const response = await fetch(`/api/boxes/${boxId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                center_x: centerX,
                center_y: centerY,
                width: boxWidth,
                height: boxHeight,
                label_name: currentBox.dataset.label
            })
        });
        
        if (!response.ok) {
            console.error('Failed to update box position');
        }
    } catch (error) {
        console.error('Error updating box position:', error);
    }
    
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDragging);
}

document.addEventListener('DOMContentLoaded', initializeDraggable);
"""


def image_card(sample: ImageDetectionSample, width: int = 200, height: int = 200) -> fh.Div:
    boxes = sample.boxes
    image_url = sample.image_url

    # Create a container with raw HTML for the boxes
    box_html = ""
    for box in boxes:
        # Calculate positions
        x = box.center_x * width
        y = box.center_y * height
        w = box.width * width
        h = box.height * height
        left = x - w / 2
        top = y - h / 2

        box_html += f"""
        <div class="draggable-box" 
             data-box-id="{box.id}"
             data-image-width="{width}"
             data-image-height="{height}"
             data-width="{box.width}"
             data-height="{box.height}"
             data-label="{box.label_name}"
             style="position:absolute; left:{left}px; top:{top}px; width:{w}px; height:{h}px; 
                    border:3px solid red; background-color:rgba(255,0,0,0.3); z-index:1000;">
        </div>
        """

    # Create the parent container with the image
    parent_div = fh.Div(style=f"position:relative; width:{width}px; height:{height}px; border:2px dashed blue;")

    img = fh.Img(src=f"{image_url}", style=f"width:{width}px; height:{height}px;")

    # Add raw HTML for boxes
    raw_html = fh.NotStr(box_html)

    return parent_div(img, raw_html)


def image_list(samples: list[ImageDetectionSample]):
    return fh.Div(*[image_card(sample) for sample in samples])


def sample_history(boxes: list[BoundingBox]):
    return fh.Div(
        fh.Ul(
            *[
                fh.Li(
                    fh.P(
                        f"ID: {box.id} (Previous: {box.previous_box_id}), Created: {box.created_at}, Center X: {box.center_x:.2f}, Center Y: {box.center_y:.2f}, Width: {box.width:.2f}, Height: {box.height:.2f}, Label: {box.label_name}, Annotator: {box.annotator_name}",
                    )
                )
                for box in boxes
            ]
        ),
    )


def sample_page(image_card: fh.Div, history: fh.Div) -> fh.Html:
    page = fh.Html(
        fh.Head(
            fh.Title("Sample image page"),
            fh.Link({"rel": "stylesheet", "href": "https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"}),
            fh.Style(
                """
                .draggable-box:hover { 
                    border-color: yellow !important;
                }
            """
            ),
            fh.Script(DRAG_SCRIPT),
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Sample image page"),
                fh.Div({"class": "grid"}, image_card, history),
            )
        ),
    )
    return page
