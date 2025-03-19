import fasthtml.common as fh
from yapml.client.navbar import navbar
from yapml.client.styles import yapml_gray_color

# JavaScript for handling database reset
RESET_DB_SCRIPT = """
document.addEventListener('DOMContentLoaded', function() {
    function resetDatabase() {
        if (!confirm('Are you sure you want to reset the database? This action cannot be undone.')) {
            return;
        }

        fetch('/api/v1/reset-db', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const feedback = document.getElementById('reset-feedback');
                feedback.textContent = 'Database reset successfully!';
                feedback.style.color = '#4caf50';
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            console.error('Error resetting database:', error);
            const feedback = document.getElementById('reset-feedback');
            feedback.textContent = 'Error: ' + error.message;
            feedback.style.color = '#f44336';
        });
    }

    // Add event listener to reset button
    document.getElementById('reset-db-btn').addEventListener('click', resetDatabase);
});
"""


def render_admin_page() -> fh.Html:
    """
    Render the admin page with database management controls.

    Returns:
        An HTML page showing admin controls
    """

    main = (
        fh.Main(
            fh.H1("Admin Panel"),
            fh.Article(
                fh.H4("Database Management"),
                fh.P("Warning: Resetting the database will delete all data and restore initial fixtures."),
                fh.Button(
                    "Reset Database",
                    id="reset-db-btn",
                ),
                fh.P(id="reset-feedback"),
                style=f"""
                    border-left: 5px solid {yapml_gray_color};
                    padding: 20px;
                    margin-bottom: 10px;
                    background-color: {yapml_gray_color}20;
                """,
            ),
            style="padding: 2rem;",
        ),
    )

    body = (
        fh.Div(
            navbar,
            main,
            style="display: grid; grid-template-columns: 150px 1fr; height: 100vh;",
        ),
    )

    page = fh.Html(
        fh.Head(
            fh.Title("Admin - Yet Another ML Platform"),
            fh.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"),
            fh.Script(RESET_DB_SCRIPT),
        ),
        fh.Body(
            body,
        ),
        data_theme="dark",
    )
    return page
