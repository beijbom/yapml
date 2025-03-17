import fasthtml.common as fh

from yamlp.datamodel import Label


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
        ),
        fh.Body(
            fh.Main(
                {"class": "container"},
                fh.H1("Labels"),
                fh.A(
                    {"href": "/samples", "style": "margin-bottom: 20px; display: inline-block;"},
                    "← All samples",
                ),
                fh.Div(
                    {"class": "grid"},
                    *[
                        fh.Article(
                            {"style": f"border-left: 5px solid {label.color}; padding-left: 15px;"},
                            fh.Div(
                                fh.H3(label.name),
                                fh.P(
                                    fh.Span(
                                        {
                                            "style": f"display: inline-block; width: 20px; height: 20px; background-color: {label.color}; margin-right: 10px; vertical-align: middle;"
                                        }
                                    ),
                                    f"Color: {label.color}",
                                ),
                                fh.P(f"Used in {len(label.boxes)} annotations"),
                            ),
                        )
                        for label in labels
                    ],
                ),
            )
        ),
    )
    return page
