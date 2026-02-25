import json

import nextmv
import plotly.graph_objects as go


def draw_sol(n, m, prob=None, x=None, y=None,
             label="Chart", coord_schools=None, coord_sites=None,
             SCHOOLS=None, SITES=None, tab_order=None) -> nextmv.Asset:
    V = list(range(n + m))
    E = []
    if tab_order is None:
        tab_order = 1

    # Get coordinates
    coordS = {i: tuple(coord_schools[i]) for i in SCHOOLS}
    coordA = {n + j: tuple(coord_sites[j]) for j in SITES}
    coord = {**coordS, **coordA}

    # Get solution if available
    if prob is not None:
        xsol = prob.getSolution(x)
        ysol = prob.getSolution(y)
        E = [(i, n + j) for i in SCHOOLS for j in SITES if xsol[i, j] > 0.5]

    # Node colors
    node_colS  = dict.fromkeys(SCHOOLS, '#5555ff')
    node_colA1 = {n + j: '#ff5555' for j in SITES if y and ysol[j] > 0.5}
    node_colA0 = {n + j: '#a0a0a0' for j in SITES if not y or ysol[j] < 0.5}
    node_col = {**node_colS, **node_colA1, **node_colA0}

    # Scatter for nodes
    node_trace = go.Scatter(
        x=[coord[i][0] for i in V],
        y=[coord[i][1] for i in V],
        mode='markers+text',
        marker={
            "size": 10,
            "color": [node_col[i] for i in V]
        },
        text=[str(i) for i in V],
        textposition="top center",
        hoverinfo='text'
    )

    # Edges as lines
    edge_traces = []
    for i, j in E:
        x0, y0 = coord[i]
        x1, y1 = coord[j]
        edge_trace = go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode='lines',
            line={"width": 1, "color": '#888'},
            hoverinfo='none'
        )
        edge_traces.append(edge_trace)

    # Layout and figure
    fig = go.Figure()
    for edge_trace in edge_traces:
        fig.add_trace(edge_trace)
    fig.add_trace(node_trace)

    fig.update_layout(
        title='School-Area Assignment Network',
        showlegend=False,
        hovermode='closest',
        margin={"b": 20, "l": 5, "r": 5, "t": 40},
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"showgrid": False, "zeroline": False},
        width=700,
        height=700
    )
#  fig.show()

# ADDED TO MAYBE MAKE WORK IN NEXTMV NEED TO CONFIRM, OTHERWISE DELETE
    json_plot = fig.to_json()

### Assets are used to render visualizations in Nextmv. THIS CAME FROM CAROLYN
    assets = nextmv.Asset(
            name="Plotly example",
            content_type="json",
            visual=nextmv.Visual(
                visual_schema=nextmv.VisualSchema(value="plotly"),
                visual_type="custom-tab",
                label=label,
                tab_order=tab_order,
            ),
            content=[json.loads(json_plot)],
        )
    return assets
