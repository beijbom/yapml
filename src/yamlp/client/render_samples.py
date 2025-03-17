from datetime import datetime

import fasthtml.common as fh
from pydantic import BaseModel

from yamlp.datamodel import BoundingBox, ObjectDetectionSample, suppress_stale_boxes

# Add JavaScript for drag and resize functionality
DRAG_SCRIPT = """
console.log('Script loaded');
let isDragging = false;
let isResizing = false;
let currentBox = null;
let currentHandle = null;
let startX, startY;
let originalLeft, originalTop, originalWidth, originalHeight;
let imageRect;
let resizeDirection = '';

function initializeDraggable() {
    console.log('Initializing draggable');
    const image = document.querySelector('img');
    imageRect = image.getBoundingClientRect();
    
    const boxes = document.querySelectorAll('.draggable-box');
    console.log('Found boxes:', boxes.length);
    boxes.forEach(box => {
        box.style.cursor = 'move';
        box.addEventListener('mousedown', startDragging);
        
        // Add event listeners to resize handles
        const handles = box.querySelectorAll('.resize-handle');
        handles.forEach(handle => {
            handle.addEventListener('mousedown', startResizing);
        });
    });
}

function startDragging(e) {
    // Ignore if clicked on a resize handle
    if (e.target.classList.contains('resize-handle')) return;
    
    isDragging = true;
    currentBox = e.target.closest('.draggable-box');
    startX = e.clientX;
    startY = e.clientY;
    originalLeft = currentBox.offsetLeft;
    originalTop = currentBox.offsetTop;
    
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDragging);
    e.preventDefault();
}

function startResizing(e) {
    isResizing = true;
    currentHandle = e.target;
    currentBox = e.target.parentElement;
    resizeDirection = currentHandle.dataset.direction;
    
    startX = e.clientX;
    startY = e.clientY;
    originalLeft = currentBox.offsetLeft;
    originalTop = currentBox.offsetTop;
    originalWidth = currentBox.offsetWidth;
    originalHeight = currentBox.offsetHeight;
    
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResizing);
    e.preventDefault();
    e.stopPropagation(); // Prevent dragging from starting
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

function resize(e) {
    if (!isResizing) return;
    
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    
    let newWidth = originalWidth;
    let newHeight = originalHeight;
    let newLeft = originalLeft;
    let newTop = originalTop;
    
    // Handle different resize directions
    switch(resizeDirection) {
        case 'nw': // top-left
            newLeft = originalLeft + dx;
            newTop = originalTop + dy;
            newWidth = originalWidth - dx;
            newHeight = originalHeight - dy;
            break;
        case 'ne': // top-right
            newTop = originalTop + dy;
            newWidth = originalWidth + dx;
            newHeight = originalHeight - dy;
            break;
        case 'sw': // bottom-left
            newLeft = originalLeft + dx;
            newWidth = originalWidth - dx;
            newHeight = originalHeight + dy;
            break;
        case 'se': // bottom-right
            newWidth = originalWidth + dx;
            newHeight = originalHeight + dy;
            break;
    }
    
    // Ensure minimum size
    if (newWidth < 10) newWidth = 10;
    if (newHeight < 10) newHeight = 10;
    
    // Apply new dimensions
    currentBox.style.width = `${newWidth}px`;
    currentBox.style.height = `${newHeight}px`;
    currentBox.style.left = `${newLeft}px`;
    currentBox.style.top = `${newTop}px`;
}

async function stopDragging() {
    if (!isDragging) return;
    isDragging = false;
    
    await updateBoxPosition();
    
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDragging);
}

async function stopResizing() {
    if (!isResizing) return;
    isResizing = false;
    
    await updateBoxPosition();
    
    document.removeEventListener('mousemove', resize);
    document.removeEventListener('mouseup', stopResizing);
}

async function updateBoxPosition() {
    const boxId = currentBox.dataset.boxId;
    const imageWidth = parseFloat(currentBox.dataset.imageWidth);
    const imageHeight = parseFloat(currentBox.dataset.imageHeight);
    
    // Calculate normalized coordinates
    const centerX = (currentBox.offsetLeft + currentBox.offsetWidth/2) / imageWidth;
    const centerY = (currentBox.offsetTop + currentBox.offsetHeight/2) / imageHeight;
    const width = currentBox.offsetWidth / imageWidth;
    const height = currentBox.offsetHeight / imageHeight;
    
    try {
        const response = await fetch(`/api/v1/boxes/${boxId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                center_x: centerX,
                center_y: centerY,
                width: width,
                height: height,
                label_name: currentBox.dataset.label
            })
        });
        
        if (!response.ok) {
            console.error('Failed to update box position');
        } else {
            // Get the updated box ID from the response and update the element
            const result = await response.json();
            if (result && result.id) {
                currentBox.dataset.boxId = result.id;
            }
            
            // Trigger HTMX to refresh the history section
            document.body.dispatchEvent(new CustomEvent('boxUpdated'));
        }
    } catch (error) {
        console.error('Error updating box position:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeDraggable);
"""

DRAG_STYLE = """
.draggable-box:hover { 
    border-color: orange !important;
}
.resize-handle {
    z-index: 20;
}
"""


def render_image_card(sample: ObjectDetectionSample, max_width: int = 500, max_height: int = 500) -> fh.Div:
    """
    Render an image with draggable and resizable bounding boxes.

    Args:
        sample: The image detection sample containing image and box data
        width: Display width of the image
        height: Display height of the image

    Returns:
        A div containing the image and interactive boxes
    """

    # Create box HTML directly to avoid issues with fh.Div
    box_html = ""
    for box in suppress_stale_boxes(sample.boxes):
        # Calculate positions in pixels
        x = box.center_x * max_width
        y = box.center_y * max_height
        w = box.width * max_width
        h = box.height * max_height
        left = x - w / 2
        top = y - h / 2

        # Create box with invisible resize handles
        box_html += f"""
        <div class="draggable-box" 
             data-box-id="{box.id}"
             data-image-width="{max_width}"
             data-image-height="{max_height}"
             data-width="{box.width}"
             data-height="{box.height}"
             data-label="{box.label_name}"
             style="position:absolute; 
                    left:{left}px; 
                    top:{top}px; 
                    width:{w}px; 
                    height:{h}px; 
                    border:2px solid red; 
                    background-color:rgba(255,0,0,0.2); 
                    box-sizing:border-box;
                    cursor:move;
                    z-index:10;">
            <!-- Invisible resize handles - just for cursor change and interaction -->
            <div class="resize-handle nw" data-direction="nw" style="position:absolute; top:-5px; left:-5px; width:10px; height:10px; cursor:nw-resize; background:transparent;"></div>
            <div class="resize-handle ne" data-direction="ne" style="position:absolute; top:-5px; right:-5px; width:10px; height:10px; cursor:ne-resize; background:transparent;"></div>
            <div class="resize-handle sw" data-direction="sw" style="position:absolute; bottom:-5px; left:-5px; width:10px; height:10px; cursor:sw-resize; background:transparent;"></div>
            <div class="resize-handle se" data-direction="se" style="position:absolute; bottom:-5px; right:-5px; width:10px; height:10px; cursor:se-resize; background:transparent;"></div>
        </div>
        """

    # Create the parent container with the image
    parent_div = fh.Div(style=f"position:relative; width:{max_width}px; height:{max_height}px;")

    img = fh.Img(src=f"{sample.url}", style=f"width:{max_width}px; height:{max_height}px;")

    # Add raw HTML for boxes
    raw_html = fh.NotStr(box_html)

    return parent_div(img, raw_html)


class BoxChange(BaseModel):
    label_name: str
    annotator_name: str
    event: str
    time_delta: str


def time_delta_string(timestamp: datetime) -> str:
    """
    Convert a timestamp to a human-readable relative time string.

    Args:
        timestamp: The datetime to convert

    Returns:
        A string like "just now", "5 seconds ago", "2 minutes ago", "3 hours ago", "2 days ago", etc.
    """
    now = datetime.now()
    delta = now - timestamp

    # Convert to total seconds
    seconds = int(delta.total_seconds())

    # Define time intervals
    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7
    month = day * 30
    year = day * 365

    if seconds < 10:
        return "just now"
    elif seconds < minute:
        return f"{seconds} seconds ago"
    elif seconds < 2 * minute:
        return "a minute ago"
    elif seconds < hour:
        return f"{seconds // minute} minutes ago"
    elif seconds < 2 * hour:
        return "an hour ago"
    elif seconds < day:
        return f"{seconds // hour} hours ago"
    elif seconds < 2 * day:
        return "yesterday"
    elif seconds < week:
        return f"{seconds // day} days ago"
    elif seconds < 2 * week:
        return "a week ago"
    elif seconds < month:
        return f"{seconds // week} weeks ago"
    elif seconds < 2 * month:
        return "a month ago"
    elif seconds < year:
        return f"{seconds // month} months ago"
    elif seconds < 2 * year:
        return "a year ago"
    else:
        return f"{seconds // year} years ago"


def boxes_to_changes(boxes: list[BoundingBox]) -> list[BoxChange]:

    box_by_id = {box.id: box for box in boxes}
    changes: list[BoxChange] = []
    for box in boxes:
        if not box.previous_box_id:
            event = "created"
        else:
            previous_box = box_by_id[box.previous_box_id]
            if previous_box.width != box.width or previous_box.height != box.height:
                event = "resized"
            elif previous_box.center_x != box.center_x or previous_box.center_y != box.center_y:
                event = "moved"
            else:
                raise ValueError(f"Unknown event for box {box} {previous_box}")
        changes.append(
            BoxChange(
                label_name=box.label_name,
                annotator_name=box.annotator_name,
                event=event,
                time_delta=time_delta_string(box.created_at),
            )
        )
    return changes


def render_sample_history(boxes: list[BoundingBox], sample_id: int):
    changes = boxes_to_changes(boxes)
    return fh.Div(
        {
            "id": "history-section",
            "hx-get": f"/samples/{sample_id}/history",
            "hx-trigger": "boxUpdated from:body",
            "hx-swap": "outerHTML",
            "style": "padding: 10px;",
        },
        fh.Ul(
            {"style": "list-style-type: none; padding-left: 0; margin: 0;"},
            *[
                fh.Li(
                    {"style": "padding: 3px 0; border-bottom: 1px solid #eee; font-size: 0.9em;"},
                    fh.Strong(f"{change.label_name} "),
                    f"{change.event} by {change.annotator_name} ",
                    fh.Small({"style": "color: #6c757d;"}, change.time_delta),
                )
                for change in changes[::-1]
            ],
        ),
    )


def render_sample_list_page(samples: list[ObjectDetectionSample]):

    page = fh.Html(
        fh.Head(
            fh.Title("Yet Another ML Platform"),
            fh.Link({"rel": "stylesheet", "href": "https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"}),
            fh.Style(DRAG_STYLE),
            fh.Script(DRAG_SCRIPT),
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Yet Another ML Platform"),
                fh.Div(
                    {"class": "grid"},
                    *[
                        fh.Div(
                            render_image_card(sample),
                            fh.A(
                                {
                                    "href": f"/samples/{sample.id}",
                                    "style": "display:block; text-align:right; margin-top:5px;",
                                },
                                f"Details →",
                            ),
                        )
                        for sample in samples
                    ],
                ),
            )
        ),
    )
    return page


def render_sample_page(sample: ObjectDetectionSample) -> fh.Html:
    history = render_sample_history(list(sample.boxes), sample.id)
    card = render_image_card(sample)

    page = fh.Html(
        fh.Head(
            fh.Title("Sample image page"),
            fh.Link({"rel": "stylesheet", "href": "https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"}),
            fh.Style(DRAG_STYLE),
            fh.Script(DRAG_SCRIPT),
            fh.Script(src="https://unpkg.com/htmx.org@1.9.6"),  # Add HTMX
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Sample image page"),
                fh.A(
                    {"href": "/samples", "style": "margin-bottom: 20px; display: inline-block;"},
                    "← All samples",
                ),
                fh.Div(
                    {
                        "class": "grid",
                        "id": "content-grid",
                    },
                    card,
                    history,
                ),
            )
        ),
    )
    return page
