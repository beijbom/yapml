import fasthtml.common as fh

from yamlp.client.styles import yamlp_gray_color

navbar = fh.Aside(
    fh.Nav(
        fh.Ul(
            fh.Li(fh.A({"href": "/samples"}, "Samples")),
            fh.Li(fh.A({"href": "/labels"}, "Labels")),
        ),
    ),
    style=f"padding: 1rem; background-color: {yamlp_gray_color}20;",
)
