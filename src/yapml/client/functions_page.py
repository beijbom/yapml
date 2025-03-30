import fasthtml.common as fh
from fasthtml.common import FT

from yapml.client.page_templates import function_template
from yapml.client.styles import yapml_gray_color
from yapml.datamodel import YapFunction

# JavaScript for handling function name edits and deletion
FUNCTION_SCRIPT = """
document.addEventListener('DOMContentLoaded', function() {
    // Function to update function
    function updateFunction(functionId, updateData) {
        fetch(`/api/v1/functions/${functionId}`, {
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
            console.log('Function updated successfully');
        })
        .catch(error => {
            console.error('Error updating function:', error);
            alert('Failed to update function. Please try again.');
            // If it was a name update, revert the text
            if (updateData.name) {
                const nameElement = document.querySelector(`[data-function-id="${functionId}"] .function-name`);
                if (nameElement) {
                    nameElement.textContent = nameElement.getAttribute('data-original-name');
                }
            }
        });
    }

    // Function to make text editable
    function makeEditable(element) {
        element.contentEditable = true;
        element.focus();
        element.setAttribute('data-original-name', element.textContent);
        
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
                const functionId = element.closest('[data-function-id]').getAttribute('data-function-id');
                updateFunction(functionId, { name: newName });
            } else if (newName === '') {
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

    // Add double-click listeners to function names
    document.querySelectorAll('.function-name').forEach(element => {
        element.addEventListener('dblclick', () => makeEditable(element));
    });

    // Function to delete function
    function deleteFunction(functionId) {
        if (!confirm('Are you sure you want to delete this function? This action cannot be undone.')) {
            return;
        }

        fetch(`/api/v1/functions/${functionId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.status === 204) {
                return null;
            } else {
                throw new Error('Network response was not ok');
            }
        })
        .then(data => {
            const functionCard = document.querySelector(`[data-function-id="${functionId}"]`);
            if (functionCard) {
                functionCard.remove();
            }
        })
        .catch(error => {
            console.error('Error deleting function:', error);
            alert('Failed to delete function. Please try again.');
        });
    }

    // Add event listeners to all delete buttons
    document.querySelectorAll('.delete-function-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            const functionId = this.getAttribute('data-function-id');
            deleteFunction(functionId);
        });
    });
});
"""


def render_function_list_page(functions: list[YapFunction]) -> FT:
    """
    Render a page that displays all functions.

    Args:
        functions: List of Function objects to display

    Returns:
        An HTML page showing all functions
    """

    main = fh.Main(
        fh.H1("Functions"),
        fh.Form(
            fh.Grid(
                fh.Input({"type": "text", "name": "name", "placeholder": "Function name", "required": True}),
                fh.Input({"type": "text", "name": "description", "placeholder": "Function description"}),
                fh.Button({"type": "submit"}, "Create Function"),
            ),
            action="/api/v1/functions-form",
            method="post",
            enctype="application/x-www-form-urlencoded",
        ),
        fh.Grid(
            *[
                fh.Article(
                    fh.A(
                        fh.Div(
                            fh.H4(
                                function.name,
                                cls="function-name",
                                style="margin: 0; cursor: pointer;",
                                title="Double-click to edit",
                            ),
                            fh.Small(
                                function.description or "No description",
                                style=f"color: {yapml_gray_color};",
                            ),
                            style="text-decoration: none; color: inherit;",
                        ),
                        href=f"/functions/{function.id}/samples",
                        style="text-decoration: none;",
                    ),
                    fh.Button(
                        "Delete",
                        cls="delete-function-btn",
                        data_function_id=f"{function.id}",
                        title="Delete function",
                    ),
                    data_function_id=f"{function.id}",
                    style=f"""
                              border-left: 5px solid {yapml_gray_color};
                              padding: 10px;
                              margin-bottom: 10px;
                              position: relative;
                              background-color: {yapml_gray_color}20;
                              cursor: pointer;
                            """,
                )
                for function in functions
            ],
        ),
        style="padding: 2rem;",
    )
    return function_template(main, 1, "Functions - Yet Another ML Platform", [FUNCTION_SCRIPT])
