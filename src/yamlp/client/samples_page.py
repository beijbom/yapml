from datetime import datetime

import fasthtml.common as fh
from pydantic import BaseModel

from yamlp.client.styles import yamlp_gray_color
from yamlp.datamodel import BoundingBox, Label, ObjectDetectionSample, suppress_stale_boxes

# Add JavaScript for drag and resize functionality
DRAG_SCRIPT = """
console.log('Script loaded');
let isDragging = false;
let isResizing = false;
let currentBox = null;
let currentHandle = null;
let startX, startY;
let originalLeft, originalTop, originalWidth, originalHeight;
let imageRect = null;
let resizeDirection = '';

// Additional variables for drag-to-create
let isDrawing = false;
let drawStartX, drawStartY;
let drawBox = null;
let selectedLabelId = null;
let currentImageContainer = null;

function initializeDraggable() {
    console.log('Initializing draggable');
    const images = document.querySelectorAll('img');
    images.forEach(image => {
        const boxes = image.parentElement.querySelectorAll('.draggable-box');
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

function initializeDrawing() {
    const images = document.querySelectorAll('img');
    images.forEach(image => {
        const imageContainer = image.parentElement;
        
        // Add drawing functionality to each image
        imageContainer.addEventListener('mousedown', startDrawing);
        imageContainer.addEventListener('mousemove', draw);
        imageContainer.addEventListener('mouseup', stopDrawing);
    });
    
    // Create hidden label selector (shared between all images)
    const labelSelector = document.createElement('select');
    labelSelector.id = 'label-selector';
    labelSelector.style.position = 'fixed';
    labelSelector.style.display = 'none';
    document.body.appendChild(labelSelector);
    
    // Update label selector options
    updateLabelSelector();
}

function updateLabelSelector() {
    const labelSelector = document.getElementById('label-selector');
    fetch('/api/v1/labels')
        .then(response => response.json())
        .then(labels => {
            // Add a prompt option
            labelSelector.innerHTML = `
                <option value="" disabled selected>Select a label</option>
                ${labels.map(label => 
                    `<option value="${label.id}" data-color="${label.color}">${label.name}</option>`
                ).join('')}
            `;
        });
}

function startDrawing(e) {
    if (e.target.tagName === 'IMG') {
        isDrawing = true;
        currentImageContainer = e.target.parentElement;
        imageRect = e.target.getBoundingClientRect();
        
        drawStartX = e.clientX - imageRect.left;
        drawStartY = e.clientY - imageRect.top;
        
        // Create the drawing box at the start position
        drawBox = document.createElement('div');
        drawBox.className = 'drawing-box';
        drawBox.style.position = 'absolute';
        drawBox.style.border = '2px dashed #fff';
        drawBox.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        drawBox.style.boxSizing = 'border-box';
        drawBox.style.width = '0';
        drawBox.style.height = '0';
        currentImageContainer.appendChild(drawBox);
        
        // Initial position will be set by the first draw event
        draw(e);
    }
}

function draw(e) {
    // Early return if we're not in a valid drawing state
    if (!isDrawing) return;
    if (!drawBox || !drawBox.parentNode) {
        // If drawBox is no longer valid, clean up the drawing state
        isDrawing = false;
        drawBox = null;
        currentImageContainer = null;
        imageRect = null;
        return;
    }
    if (!currentImageContainer || e.target.parentElement !== currentImageContainer) return;
    
    console.log('Raw event:', {
        clientX: e.clientX,
        clientY: e.clientY,
        target: e.target.tagName,
        imageRect: {
            left: imageRect.left,
            top: imageRect.top
        }
    });
    
    const currentX = e.clientX - imageRect.left;
    const currentY = e.clientY - imageRect.top;
    
    console.log('Calculated position:', {
        currentX,
        currentY,
        drawStartX,
        drawStartY
    });
    
    // Calculate raw dimensions first
    const width = Math.abs(currentX - drawStartX);
    const height = Math.abs(currentY - drawStartY);
    
    // Calculate position, adjusting for minimum size if needed
    let left = Math.min(currentX, drawStartX);
    let top = Math.min(currentY, drawStartY);
    
    // Store current box reference to ensure it exists throughout the animation frame
    const currentDrawBox = drawBox;
    
    // Update box position and size in a single batch
    requestAnimationFrame(() => {
        if (currentDrawBox && currentDrawBox.parentNode) {
            currentDrawBox.style.left = `${left}px`;
            currentDrawBox.style.top = `${top}px`;
            currentDrawBox.style.width = `${width}px`;
            currentDrawBox.style.height = `${height}px`;
        }
    });
}

async function stopDrawing(e) {
    if (!isDrawing || !drawBox) return;
    isDrawing = false;
    
    // Store references before we clear them
    const finalDrawBox = drawBox;
    const finalImageContainer = currentImageContainer;
    
    const endX = e.clientX - imageRect.left;
    const endY = e.clientY - imageRect.top;
    
    // Clear global state immediately
    drawBox = null;
    currentImageContainer = null;
    imageRect = null;
    
    // Only show label selector if box is big enough
    if (Math.abs(endX - drawStartX) > 10 && Math.abs(endY - drawStartY) > 10) {
        // Store box dimensions before showing selector
        const boxDimensions = {
            left: parseFloat(finalDrawBox.style.left),
            top: parseFloat(finalDrawBox.style.top),
            width: parseFloat(finalDrawBox.style.width),
            height: parseFloat(finalDrawBox.style.height)
        };
        
        // Position and show label selector
        const labelSelector = document.getElementById('label-selector');
        if (!labelSelector) {
            console.error('Label selector not found');
            if (finalDrawBox && finalDrawBox.parentNode) {
                finalDrawBox.remove();
            }
            return;
        }
        
        labelSelector.style.left = e.clientX + 'px';
        labelSelector.style.top = e.clientY + 'px';
        labelSelector.style.display = 'block';
        
        // Remove any existing onchange handler
        labelSelector.onchange = null;
        
        // Create new onchange handler with access to stored state
        labelSelector.onchange = async () => {
            const labelId = labelSelector.value;
            if (!labelId) return;  // Skip if no label selected
            
            // Verify we still have access to the image container
            if (!finalImageContainer) {
                console.error('Image container no longer available');
                labelSelector.style.display = 'none';
                if (finalDrawBox && finalDrawBox.parentNode) {
                    finalDrawBox.remove();
                }
                return;
            }
            
            const imageElement = finalImageContainer.querySelector('img');
            if (!imageElement) {
                console.error('Image element not found');
                labelSelector.style.display = 'none';
                if (finalDrawBox && finalDrawBox.parentNode) {
                    finalDrawBox.remove();
                }
                return;
            }
            
            const imageWidth = imageElement.width;
            const imageHeight = imageElement.height;
            // Look for sample ID on the image container itself now
            const sampleId = finalImageContainer.getAttribute('data-sample-id');
            
            if (!sampleId) {
                console.error('Sample ID not found on image container');
                labelSelector.style.display = 'none';
                if (finalDrawBox && finalDrawBox.parentNode) {
                    finalDrawBox.remove();
                }
                return;
            }
            
            console.log('Creating box with:', {
                sampleId,
                labelId,
                imageWidth,
                imageHeight,
                boxDimensions
            });
            
            // Calculate normalized coordinates using stored dimensions
            const centerX = (boxDimensions.left + boxDimensions.width/2) / imageWidth;
            const centerY = (boxDimensions.top + boxDimensions.height/2) / imageHeight;
            const normalizedWidth = boxDimensions.width / imageWidth;
            const normalizedHeight = boxDimensions.height / imageHeight;
            
            const payload = {
                sample_id: parseInt(sampleId),
                label_id: parseInt(labelId),
                center_x: centerX,
                center_y: centerY,
                width: normalizedWidth,
                height: normalizedHeight
            };
            
            console.log('Sending payload:', payload);
            
            // Create the box
            try {
                const response = await fetch('/api/v1/boxes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`Failed to create box: ${JSON.stringify(errorData)}`);
                }
                
                // Refresh the page to show new box
                window.location.reload();
            } catch (error) {
                console.error('Error creating box:', error);
                alert('Failed to create box. Please check console for details.');
            } finally {
                // Hide selector and remove drawing box
                labelSelector.style.display = 'none';
                if (finalDrawBox && finalDrawBox.parentNode) {
                    finalDrawBox.remove();
                }
            }
        };
    } else {
        if (finalDrawBox && finalDrawBox.parentNode) {
            finalDrawBox.remove();
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeDraggable();
    initializeDrawing();
});
"""

DRAG_STYLE = """
.draggable-box:hover { 
    border-color: orange !important;
}
.resize-handle {
    z-index: 20;
}
#label-selector {
    padding: 8px;
    border-radius: 6px;
    background: var(--card-background-color);
    color: var(--color);
    border: 1px solid var(--card-sectionning-background-color);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    font-size: 14px;
    min-width: 20px;
    max-width: 120px;
    z-index: 1000;
    position: fixed;
    cursor: pointer;
}
#label-selector option {
    padding: 4px 8px;
    cursor: pointer;
}
#label-selector option:hover {
    background-color: var(--primary);
}
"""


def render_box(box, max_width, max_height):
    # Calculate positions in pixels
    x = box.center_x * max_width
    y = box.center_y * max_height
    w = box.width * max_width
    h = box.height * max_height
    left = x - w / 2
    top = y - h / 2

    # Create the box with all its components
    return fh.Div(
        {
            "data-box-id": str(box.id),
            "data-image-width": str(max_width),
            "data-image-height": str(max_height),
            "data-width": str(box.width),
            "data-height": str(box.height),
            "data-label": box.label.name,
        },
        cls="draggable-box",
        style=f"""
                position: absolute;
                left: {left}px;
                top: {top}px;
                width: {w}px;
                height: {h}px;
                border: 2px solid {box.label.color};
                    background-color: {box.label.color}20;
                box-sizing: border-box;
                cursor: move;
                z-index: 10;
            """,
        *[
            fh.Div(
                box.label.name,
                style="""
                position: absolute;
                bottom: 0px;
                left: 0;
                background-color: rgba(0,0,0,0.7);
                color: white;
                padding: 1px 5px;
                font-size: 10px;
                border-radius: 3px;
                font-family: sans-serif;
                z-index: 15;
            """,
            ),
            # Resize handles
            fh.Div(
                {"data-direction": "nw"},
                style="position:absolute; top:-5px; left:-5px; width:10px; height:10px; cursor:nw-resize; background:transparent;",
                cls="resize-handle nw",
            ),
            fh.Div(
                {"data-direction": "ne"},
                style="position:absolute; top:-5px; right:-5px; width:10px; height:10px; cursor:ne-resize; background:transparent;",
                cls="resize-handle ne",
            ),
            fh.Div(
                {"data-direction": "sw"},
                style="position:absolute; bottom:-5px; left:-5px; width:10px; height:10px; cursor:sw-resize; background:transparent;",
                cls="resize-handle sw",
            ),
            fh.Div(
                {"data-direction": "se"},
                style="position:absolute; bottom:-5px; right:-5px; width:10px; height:10px; cursor:se-resize; background:transparent;",
                cls="resize-handle se",
            ),
        ],
    )


def render_image_card(sample: ObjectDetectionSample, max_width: int = 500, max_height: int = 500) -> fh.Div:
    """
    Render an image with draggable and resizable bounding boxes.
    """
    return fh.Div(
        fh.Img(src=f"{sample.url}", style=f"width:{max_width}px; height:{max_height}px;"),
        *[render_box(box, max_width, max_height) for box in suppress_stale_boxes(sample.boxes)],
        style=f"position:relative; width:{max_width}px; height:{max_height}px;",
        **{"data-sample-id": str(sample.id)},
    )


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
                continue  # Skip if no changes
        changes.append(
            BoxChange(
                label_name=box.label.name,
                annotator_name=box.annotator_name,
                event=event,
                time_delta=time_delta_string(box.created_at),
            )
        )
    return changes


def render_sample_history(boxes: list[BoundingBox], sample_id: int):
    changes = boxes_to_changes(boxes)
    return fh.Div(
        fh.Ul(
            *[
                fh.Li(
                    fh.Strong(f"{change.label_name} "),
                    f"{change.event} by {change.annotator_name} ",
                    fh.Small(change.time_delta, style=f"color: {yamlp_gray_color};"),
                    style="padding: 3px 0; font-size: 0.9em;",
                )
                for change in changes[::-1]
            ],
        ),
        id="history-section",
        hx_get=f"/samples/{sample_id}/history",
        hx_trigger="boxUpdated from:body",
        hx_swap="outerHTML",
    )


def render_sample_list_page(samples: list[ObjectDetectionSample]):

    page = fh.Html(
        fh.Head(
            fh.Title("Samples"),
            fh.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"),
            fh.Style(DRAG_STYLE),
            fh.Script(DRAG_SCRIPT),
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Yet Another ML Platform"),
                fh.Nav(
                    fh.Ul(
                        fh.Li(fh.A({"href": "/samples"}, "Samples")),
                        fh.Li(fh.A({"href": "/labels"}, "Labels")),
                    ),
                ),
                fh.Grid(
                    *[
                        fh.Div(
                            render_image_card(sample),
                            fh.A(
                                "Details →",
                                href=f"/samples/{sample.id}",
                                style="display:block; text-align:left; margin-top:5px;",
                            ),
                        )
                        for sample in samples
                    ],
                ),
            ),
        ),
        data_theme="dark",
    )
    return page


def render_sample_page(sample: ObjectDetectionSample, labels: list[Label]) -> fh.Html:
    history = render_sample_history(list(sample.boxes), sample.id)
    card = render_image_card(sample)

    page = fh.Html(
        fh.Head(
            fh.Title("Sample image page"),
            fh.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"),
            fh.Style(DRAG_STYLE),
            fh.Script(DRAG_SCRIPT),
            fh.Script(src="https://unpkg.com/htmx.org@1.9.6"),
        ),
        fh.Body(
            fh.Main(
                fh.H1("Sample image page"),
                fh.Nav(
                    fh.Ul(
                        fh.Li(fh.A({"href": "/samples"}, "Samples")),
                        fh.Li(fh.A({"href": "/labels"}, "Labels")),
                    ),
                ),
                fh.Grid(
                    card,  # Remove outer div since sample ID is now in render_image_card
                    history,
                    style="grid-template-columns: 3fr 1fr",
                ),
                cls="container",
            ),
        ),
        data_theme="dark",
    )
    return page
