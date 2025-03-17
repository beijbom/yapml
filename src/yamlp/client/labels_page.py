import fasthtml.common as fh

from yamlp.client.styles import yamlp_gray_color
from yamlp.datamodel import Label, suppress_stale_boxes

# JavaScript for handling color changes and name edits
COLOR_CHANGE_SCRIPT = """
document.addEventListener('DOMContentLoaded', function() {
    // Function to update label
    function updateLabel(labelId, updateData) {
        fetch(`/api/v1/labels/${labelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Label updated successfully');
        })
        .catch(error => {
            console.error('Error updating label:', error);
            alert('Failed to update label. Please try again.');
            // If it was a name update, revert the text
            if (updateData.name) {
                const nameElement = document.querySelector(`[data-label-id="${labelId}"] .label-name`);
                if (nameElement) {
                    nameElement.textContent = nameElement.getAttribute('data-original-name');
                }
            }
            // If it was a color update, revert the color
            if (updateData.color) {
                const picker = document.querySelector(`.label-color-picker[data-label-id="${labelId}"]`);
            }
        });
    }

    // Function to make text editable
    function makeEditable(element) {
        element.contentEditable = true;
        element.focus();
        // Store original text in case we need to revert
        element.setAttribute('data-original-name', element.textContent);
        
        // Select all text
        const range = document.createRange();
        range.selectNodeContents(element);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        function handleBlur() {
            element.contentEditable = false;
            const newName = element.textContent.trim();
            const originalName = element.getAttribute('data-original-name');
            
            if (newName !== originalName && newName !== '') {
                const labelId = element.closest('[data-label-id]').getAttribute('data-label-id');
                updateLabel(labelId, { name: newName });
            } else if (newName === '') {
                // If empty, revert to original name
                element.textContent = originalName;
            }
            
            element.removeEventListener('blur', handleBlur);
            element.removeEventListener('keydown', handleKeydown);
        }

        function handleKeydown(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                element.blur();
            } else if (e.key === 'Escape') {
                element.textContent = element.getAttribute('data-original-name');
                element.blur();
            }
        }

        element.addEventListener('blur', handleBlur);
        element.addEventListener('keydown', handleKeydown);
    }

    // Add double-click listeners to label names
    document.querySelectorAll('.label-name').forEach(element => {
        element.addEventListener('dblclick', () => makeEditable(element));
    });

    // Function to update label color
    function updateLabelColor(labelId, newColor) {
        updateLabel(labelId, { color: newColor });
    }

    // Function to delete label
    function deleteLabel(labelId) {
        if (!confirm('Are you sure you want to delete this label? This action cannot be undone.')) {
            return;
        }

        fetch(`/api/v1/labels/${labelId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove the label card from the UI
            const labelCard = document.querySelector(`[data-label-id="${labelId}"]`);
            if (labelCard) {
                labelCard.remove();
            }
        })
        .catch(error => {
            console.error('Error deleting label:', error);
            alert('Failed to delete label. Please try again.');
        });
    }

    // Add event listeners to all color pickers
    document.querySelectorAll('.label-color-picker').forEach(picker => {
        // Store the original color
        picker.setAttribute('data-original-color', picker.value);
        
        // Submit the color change on change (when picker is closed)
        picker.addEventListener('change', function(event) {
            const labelId = this.getAttribute('data-label-id');
            const newColor = this.value;
            // Update the stored original color
            this.setAttribute('data-original-color', newColor);
            updateLabelColor(labelId, newColor);
        });
    });

    // Add event listeners to all delete buttons
    document.querySelectorAll('.delete-label-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            const labelId = this.getAttribute('data-label-id');
            deleteLabel(labelId);
        });
    });
});
"""


def render_label_list_page(labels: list[Label]) -> fh.Html:
    """
    Render a page that displays all labels with their colors.

    Args:
        labels: List of Label objects to display

    Returns:
        An HTML page showing all labels
    """
    page = fh.Html(
        fh.Head(
            fh.Title("Labels - Yet Another ML Platform"),
            fh.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"),
            fh.Script(COLOR_CHANGE_SCRIPT),
        ),
        fh.Body(
            fh.Main(
                fh.H1("Labels"),
                fh.Nav(
                    fh.Ul(
                        fh.Li(fh.A({"href": "/samples"}, "Samples")),
                        fh.Li(fh.A({"href": "/labels"}, "Labels")),
                    ),
                ),
                fh.Form(
                    fh.Grid(
                        fh.Input({"type": "text", "name": "name", "placeholder": "Label name", "required": True}),
                        fh.Input({"type": "color", "name": "color", "value": "#000000", "required": True}),
                        fh.Button({"type": "submit"}, "Create Label"),
                    ),
                    action="/api/v1/labels-form",
                    method="post",
                    enctype="application/x-www-form-urlencoded",
                ),
                fh.Grid(
                    *[
                        fh.Article(
                            fh.Div(
                                fh.H4(
                                    label.name,
                                    cls="label-name",
                                    style="margin: 0; cursor: pointer;",
                                    title="Double-click to edit",
                                ),
                                fh.Input(
                                    type="color",
                                    cls="label-color-picker",
                                    value=label.color,
                                    data_label_id=f"{label.id}",
                                ),
                                fh.Small(
                                    f"{len(suppress_stale_boxes(label.boxes))} annotations",
                                    style=f"margin-left: auto; color: {yamlp_gray_color};",
                                ),
                            ),
                            fh.Button(
                                "Delete",
                                cls="delete-label-btn",
                                data_label_id=f"{label.id}",
                                title="Delete label",
                            ),
                            data_label_id=f"{label.id}",
                            style=f"""
                                border-left: 5px solid {yamlp_gray_color};
                                padding: 10px;
                                margin-bottom: 10px;
                                position: relative;
                                background-color: {yamlp_gray_color}20;
                            """,
                        )
                        for label in labels
                    ],
                ),
                cls="container",
            )
        ),
    )
    return page
