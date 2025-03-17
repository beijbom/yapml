import fasthtml.common as fh

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
        
        // Preview the color change on input (before submitting)
        picker.addEventListener('input', function(event) {
            const labelId = this.getAttribute('data-label-id');
            const newColor = this.value;
            const labelCard = document.querySelector(`[data-label-id="${labelId}"]`); 
        });
        
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
            fh.Link({"rel": "stylesheet", "href": "https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"}),
            fh.Script(COLOR_CHANGE_SCRIPT),
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Labels"),
                fh.Nav(
                    {"style": "margin-bottom: 20px;"},
                    fh.Ul(
                        fh.Li(fh.A({"href": "/samples"}, "Samples")),
                        fh.Li(fh.A({"href": "/labels"}, "Labels")),
                    ),
                ),
                fh.Article(
                    {"style": "margin-bottom: 20px;"},
                    fh.Form(
                        {
                            "action": "/api/v1/labels",
                            "method": "post",
                            "enctype": "application/x-www-form-urlencoded",
                        },
                        fh.Div(
                            {"class": "grid"},
                            fh.Input({"type": "text", "name": "name", "placeholder": "Label name", "required": True}),
                            fh.Input({"type": "color", "name": "color", "value": "#000000", "required": True}),
                            fh.Button({"type": "submit"}, "Create Label"),
                        ),
                    ),
                ),
                fh.Div(
                    {"class": "grid"},
                    *[
                        fh.Article(
                            {
                                "style": f"""
                                    border-left: 5px solid {label.color}; 
                                    padding: 10px; 
                                    margin-bottom: 10px; 
                                    position: relative;
                                    background-color: {label.color}20;
                                """.replace(
                                    "\n", ""
                                ),
                                "data-label-id": f"{label.id}",
                            },
                            fh.Div(
                                {"style": "display: flex; align-items: center; gap: 10px;"},
                                fh.H4(
                                    {
                                        "style": "margin: 0; cursor: pointer;",
                                        "class": "label-name",
                                        "title": "Double-click to edit",
                                    },
                                    label.name,
                                ),
                                fh.Input(
                                    {
                                        "type": "color",
                                        "value": label.color,
                                        "class": "label-color-picker",
                                        "data-label-id": f"{label.id}",
                                        "style": "width: 30px; height: 30px; padding: 0; border: none; cursor: pointer;",
                                    }
                                ),
                                fh.Small(
                                    {"style": "margin-left: auto; color: #6c757d;"},
                                    f"{len(suppress_stale_boxes(label.boxes))} annotations",
                                ),
                            ),
                            fh.Button(
                                {
                                    "class": "delete-label-btn",
                                    "data-label-id": f"{label.id}",
                                    "style": """
                                        position: absolute;
                                        bottom: 5px;
                                        right: 5px;
                                        background: none;
                                        border: none;
                                        padding: 5px;
                                        cursor: pointer;
                                        color: #6c757d;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        transition: color 0.2s;
                                        opacity: 0.6;
                                    """.replace(
                                        "\n", ""
                                    ),
                                    "title": "Delete label",
                                    "onmouseover": "this.style.opacity='1'; this.style.color='#dc3545'",
                                    "onmouseout": "this.style.opacity='0.6'; this.style.color='#6c757d'",
                                },
                                fh.NotStr(
                                    """
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                        <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                                    </svg>
                                """
                                ),
                            ),
                        )
                        for label in labels
                    ],
                ),
            )
        ),
    )
    return page
