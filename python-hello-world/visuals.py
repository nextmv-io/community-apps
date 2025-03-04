import plotly.graph_objects as go
import json
import nextmv

def create_visuals(name: str, radius: float, distance: float) -> any:
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[name],
            y=[radius],
            name='Radius (km)',
            marker_color='red',
            opacity=0.5
        )
    )
    fig.add_trace(
        go.Bar(
            x=[name],
            y=[distance],
            name='Distance (Millions km)',
            marker_color='blue',
            opacity=0.5
        )
    )
    fig.update_layout(
        title='Radius and Distance by Planet',
        xaxis_title='Planet',
        yaxis_title='Values',
        barmode='group'
    )

    fig = fig.to_json()
    
    assets=[
        {
            "name": "Plotly example",
            "content_type": "json",
            "visual": {
            "schema": "plotly",
            "type": "custom-tab",
            "label": "Charts"
            },
            "content": [
            json.loads(fig)
            ]
        }
    ]
    
    return assets