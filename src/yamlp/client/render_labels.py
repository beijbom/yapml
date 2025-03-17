import fasthtml.common as fh

from yamlp.datamodel import Label

# JavaScript for handling color changes
COLOR_CHANGE_SCRIPT = """
document.addEventListener('DOMContentLoaded', function() {
    // Function to update label color
    function updateLabelColor(labelId, newColor) {
        fetch(`/api/v1/labels/${labelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ color: newColor })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update was successful - no need to do anything as the border is already updated
            console.log('Label color updated successfully');
        })
        .catch(error => {
            console.error('Error updating label color:', error);
            alert('Failed to update label color. Please try again.');
            // Revert the color picker to the original color
            const picker = document.querySelector(`.label-color-picker[data-label-id="${labelId}"]`);
            if (picker) {
                picker.value = picker.getAttribute('data-original-color');
                // Also revert the border color
                const labelCard = document.querySelector(`[data-label-id="${labelId}"]`);
                if (labelCard) {
                    labelCard.style.borderLeftColor = picker.getAttribute('data-original-color');
                }
            }
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
            if (labelCard) {
                labelCard.style.borderLeftColor = newColor;
            }
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
                fh.Div(
                    {"class": "grid"},
                    *[
                        fh.Article(
                            {
                                "style": f"border-left: 5px solid {label.color}; padding: 10px; margin-bottom: 10px;",
                                "data-label-id": f"{label.id}",
                            },
                            fh.Div(
                                {"style": "display: flex; align-items: center; gap: 10px;"},
                                fh.H4({"style": "margin: 0;"}, label.name),
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
                                    {"style": "margin-left: auto; color: #6c757d;"}, f"{len(label.boxes)} annotations"
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
