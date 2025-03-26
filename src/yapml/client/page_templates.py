import fasthtml.common as fh

from yapml.client.navbar import navbar


def function_template(main: fh.Html, title: str, scripts: list[str] = None, styles: list[str] = None) -> fh.Html:
    scripts = [] if not scripts else scripts
    styles = [] if not styles else styles
    body = (
        fh.Div(
            navbar,
            main,
            style="display: grid; grid-template-columns: 150px 1fr; height: 100vh;",
        ),
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
