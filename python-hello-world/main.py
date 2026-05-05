import json

import nextmv
import plotly.graph_objects as go


def main():
    """Main function that runs the model."""

    # Read the input.
    loaded_input = nextmv.load()
    name = loaded_input.data["name"]
    options = loaded_input.options

    ##### Insert model here

    # Print logs that render in the run view in Nextmv Console.
    message = f"Hello, {name}"
    nextmv.log(message)

    if options.details:
        detail = f"You are {loaded_input.data['distance']} million km from the sun"
        nextmv.log(detail)

    assets = _create_visuals(name, loaded_input.data["radius"], loaded_input.data["distance"])

    # Write output and metrics.
    nextmv.write(
        options=options,
        solution={"message": message},
        metrics={
            "value": 1.23,
            "message": message,
        },
        assets=assets,
    )


def _create_visuals(name: str, radius: float, distance: float) -> list[nextmv.Asset]:
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


if __name__ == "__main__":
    main()
