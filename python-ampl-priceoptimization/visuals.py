import json
from typing import Any

import nextmv
import plotly.graph_objects as go


def create_visuals(solutions: dict, metrics: dict[str, Any]) -> list[nextmv.Asset]:
    regions = solutions["regions"]
    prices = tuple(solutions["price"].values())
    quantities = tuple(solutions["quantity"].values())
    demand_forecast = tuple(metrics["expected_demand"].values())

    # Added sales & waste data
    sales = tuple(metrics["expected_sales"].values())
    waste = tuple(metrics["expected_waste"].values())

    # First figure: Price & Quantity
    fig_forecast_quantities = go.Figure()
    fig_forecast_quantities.add_trace(
        go.Bar(x=regions, y=quantities, name="Quantity", marker_color="red", opacity=0.5),
    )
    fig_forecast_quantities.add_trace(
        go.Bar(x=regions, y=demand_forecast, name="Demand Forecast", marker_color="green", opacity=0.5),
    )
    fig_forecast_quantities.update_layout(
        title="Demand and Quantity Allocated by Region",
        xaxis_title="Regions",
        yaxis_title="Millions of Avocados",
        barmode="group",
    )
    fig_forecast_quantities_json = fig_forecast_quantities.to_json()

    # Second figure: Demand Forecast
    fig_prices = go.Figure()
    fig_prices.add_trace(
        go.Bar(x=regions, y=prices, name="Price ($)", marker_color="blue", opacity=0.5),
    )
    fig_prices.update_layout(
        title="Price of Avocados by Region",
        xaxis_title="Regions",
        yaxis_title="Price ($)",
        barmode="group",
    )
    fig_prices_json = fig_prices.to_json()

    # Third figure: Sales & Waste
    fig_sales_waste = go.Figure()
    fig_sales_waste.add_trace(
        go.Bar(x=regions, y=sales, name="Sales", marker_color="purple", opacity=0.5),
    )
    fig_sales_waste.add_trace(
        go.Bar(x=regions, y=waste, name="Waste", marker_color="orange", opacity=0.5),
    )
    fig_sales_waste.update_layout(
        title="Sales and Waste by Region",
        xaxis_title="Regions",
        yaxis_title="Values",
        barmode="group",
    )
    fig_sales_waste_json = fig_sales_waste.to_json()

    # Build the Nextmv output object
    assets = [
        nextmv.Asset(
            name="Plotly example",
            content_type="json",
            visual=nextmv.Visual(
                visual_schema=nextmv.VisualSchema.PLOTLY,
                visual_type="custom-tab",
                label="pricing charts",
            ),
            content=[
                json.loads(fig_forecast_quantities_json),
                json.loads(fig_prices_json),
                json.loads(fig_sales_waste_json),
            ],
        ),
    ]

    return assets
