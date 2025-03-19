import fasthtml.common as fh
from yapml.client.styles import yapml_gray_color

navbar = fh.Aside(
    fh.Nav(
        fh.Ul(
            fh.Li(fh.A({"href": "/samples"}, "Samples")),
            fh.Li(fh.A({"href": "/labels"}, "Labels")),
        ),
    ),
    style=f"padding: 1rem; background-color: {yapml_gray_color}20;",
)
