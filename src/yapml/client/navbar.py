import fasthtml.common as fh
from fasthtml.common import FT

from yapml.client.styles import yapml_gray_color


def render_navbar(function_id: int) -> FT:
    navbar = fh.Aside(
        fh.Nav(
            fh.Ul(
                fh.Li(fh.A({"href": f"/functions/{function_id}/samples"}, "Samples")),
                fh.Li(fh.A({"href": f"/functions/{function_id}/labels"}, "Labels")),
                fh.Li(fh.A({"href": f"/functions/{function_id}/admin"}, "Admin")),
                fh.Li(fh.A({"href": "/docs"}, "Docs")),
            ),
        ),
        style=f"padding: 1rem; background-color: {yapml_gray_color}20;",
    )
    return navbar
