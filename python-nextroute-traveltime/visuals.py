import json

import nextmv
import plotly.graph_objects as go


def create_visuals(name: str, radius: float, distance: float) -> list[nextmv.Asset]:
    """Create a Plotly bar chart with radius and distance for a planet."""

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=[name], y=[radius], name="Radius (km)", marker_color="red", opacity=0.5),
    )
    fig.add_trace(
        go.Bar(x=[name], y=[distance], name="Distance (Millions km)", marker_color="blue", opacity=0.5),
    )
    fig.update_layout(
        title="Radius and Distance by Planet", xaxis_title="Planet", yaxis_title="Values", barmode="group"
    )
    fig = fig.to_json()

    assets = [
        nextmv.Asset(
            name="Plotly example",
            content_type="json",
            visual=nextmv.Visual(
                visual_schema=nextmv.VisualSchema.PLOTLY,
                visual_type="custom-tab",
                label="Charts",
            ),
            content=[json.loads(fig)],
        )
    ]

    return assets
