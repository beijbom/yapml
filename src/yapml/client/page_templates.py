from typing import Optional

import fasthtml.common as fh
from fasthtml.common import FT

from yapml.client.navbar import render_navbar


def function_template(
    main: FT,
    function_id: int,
    title: str,
    scripts: Optional[list[str]] = None,
    styles: Optional[list[str]] = None,
) -> FT:
    scripts = [] if not scripts else scripts
    styles = [] if not styles else styles
    body = fh.Div(
        render_navbar(function_id),
        main,
        style="display: grid; grid-template-columns: 150px 1fr; height: 100vh;",
    )

    page = fh.Html(
        fh.Head(
            fh.Title(title),
            fh.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css"),
            fh.Script(src="https://unpkg.com/htmx.org@1.9.6"),
            *[fh.Script(script) for script in scripts],
            *[fh.Style(style) for style in styles],
            fh.Body(body),
        ),
        data_theme="dark",
    )
    return page
