import colorsys
import copy
import json

import nextmv
import pandas as pd
import plotly.express
import requests
from nextpipe import FlowSpec, app, needs, step

POLYGON_URL = "https://gist.githubusercontent.com/merschformann/74f34f9b9cd21b624586035dfe015ec5/raw/952b0f6574713d7c7e79638bee46aa6918bcc35d/plz-filtered.geojson"


# >>> Workflow definition
class Flow(FlowSpec):
    @step
    def fetch_regions(_: dict):
        """Downloads complementary regional information."""
        result = requests.get(POLYGON_URL)
        result.raise_for_status()
        regions = result.json()
        return regions

    @app(app_id="region-allocation")
    @step
    def solve():
        """Runs the model."""
        pass  # Execution happens in sub-app.

    @needs(predecessors=[solve, fetch_regions])
    @step
    def bundle_assets(result: dict, geojson_regions: dict):
        """Enhances the result."""

        # Colorize the regions based on the assignment and add metadata as a popup.
        assignment_asset = copy.deepcopy(geojson_regions)
        geojson_assignment(result, assignment_asset)

        # Create choropleth map of the regions and their demand.
        demand_asset = copy.deepcopy(geojson_regions)
        geojson_demand(result, demand_asset)

        # Create bar plot of the hub utilization
        utilization_asset = create_utilization_plot(result)

        # Write out the result
        return nextmv.Output(
            json_configurations={
                "indent": None,
                "separators": (",", ":"),
            },
            solution=result["solution"],
            statistics=result["statistics"],
            assets=[
                nextmv.Asset(
                    name="regions",
                    content_type="json",
                    visual=nextmv.Visual(
                        visual_schema=nextmv.VisualSchema(value=nextmv.VisualSchema.GEOJSON),
                        label="Assignment",
                        visual_type="custom-tab",
                    ),
                    content=assignment_asset,
                ),
                nextmv.Asset(
                    name="demand",
                    content_type="json",
                    visual=nextmv.Visual(
                        visual_schema=nextmv.VisualSchema(value=nextmv.VisualSchema.GEOJSON),
                        label="Demand",
                        visual_type="custom-tab",
                    ),
                    content=demand_asset,
                ),
                nextmv.Asset(
                    name="utilization",
                    content_type="json",
                    visual=nextmv.Visual(
                        visual_schema=nextmv.VisualSchema(value=nextmv.VisualSchema.PLOTLY),
                        label="Utilization",
                        visual_type="custom-tab",
                    ),
                    content=utilization_asset,
                ),
            ],
        )


def main():
    # Load input data
    input = nextmv.load()

    # Run workflow
    flow = Flow("DecisionFlow", input.data)
    flow.run()

    # Write out the result
    nextmv.write(flow.get_result(flow.bundle_assets))


def geojson_assignment(
    result: dict,
    regions: dict,
) -> None:
    """Colorizes the regions based on the assignment and adds metadata as a popup."""
    # Remove regions that are not in the solution
    solution_regions = set(result["solution"]["assignments"].keys())
    for region in list(regions["features"]):
        if region["properties"]["plz"] not in solution_regions:
            regions["features"].remove(region)

    # Set colors for the hubs
    hub_ids = [hub["id"] for hub in result["solution"]["hubs"]]
    hues = {hub: i / len(hub_ids) for i, hub in enumerate(hub_ids)}
    hub_plzs = {hub["plz"] for hub in result["solution"]["hubs"]}

    # Get region polygons
    region_polygons = {feature["properties"]["plz"]: feature for feature in regions["features"]}

    # Get additional information
    region_info = {region["plz"]: region for region in result["solution"]["regions"]}
    hub_info = {hub["plz"]: hub for hub in result["solution"]["hubs"]}

    # Set color and metadata for each region
    for region, hub in result["solution"]["assignments"].items():
        # Get the region polygon
        region_polygon = region_polygons[region]
        is_hub = region in hub_plzs
        # Set the color based on the hub
        hue = hues[hub]
        saturation = 0.9 if is_hub else 0.6
        value = 0.8
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        rgbhex = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        # Set ID for the feature
        region_polygon["id"] = region
        # Set the style for the region polygon
        region_polygon["properties"]["style"] = {
            "weight": 1,
            "color": "#000000",
            "opacity": 1,
            "fillColor": rgbhex,
            "fillOpacity": 0.7 if is_hub else 0.5,
        }
        # Add metadata to the region polygon
        metadata = [
            {"key": "hub", "value": hub},
            {"key": "region", "value": region},
            {"key": "plz", "value": region_info[region]["plz"]},
            {"key": "demand", "value": region_info[region]["demand"]},
        ]
        if is_hub:
            metadata.extend(
                [
                    {"key": "capacity", "value": hub_info[region]["capacity"]},
                    {"key": "hub_id", "value": hub_info[region]["id"]},
                    {"key": "hub_name", "value": hub_info[region]["name"]},
                ]
            )
        region_polygon["properties"]["metadata"] = metadata


def value_to_color(value):
    """Converts a value in the range [0, 1] to a hex color code using the Plasma color scale."""
    value = max(0, min(1, value))
    plasma_colors = plotly.express.colors.sequential.Plasma
    index = int(value * (len(plasma_colors) - 1))
    return plasma_colors[index]


def geojson_demand(
    result: dict,
    geojson: dict,
) -> None:
    """Creates geojson for a choropleth map of the regions and their demand."""
    # Prepare data.
    solution = result["solution"]
    region_info = {region["plz"]: region for region in result["solution"]["regions"]}
    hub_info = {hub["plz"]: hub for hub in result["solution"]["hubs"]}
    region_polygons = {feature["properties"]["plz"]: feature for feature in geojson["features"]}
    hub_plzs = {hub["plz"] for hub in result["solution"]["hubs"]}
    max_demand = max(region["demand"] for region in solution["regions"])

    # Calculate normalized demand and set color for each region
    for region, hub in solution["assignments"].items():
        # Get the region polygon
        region_polygon = region_polygons[region]
        # Normalize the demand
        normalized_demand = region_info[region]["demand"] / max_demand
        # Set the color for the region polygon
        color = value_to_color(normalized_demand)
        # Set the style for the region polygon
        region_polygon["properties"]["style"] = {
            "weight": 1,
            "color": "#000000",
            "opacity": 1,
            "fillColor": color,
            "fillOpacity": 0.7,
        }
        # Add metadata to the region polygon
        metadata = [
            {"key": "hub", "value": hub},
            {"key": "region", "value": region},
            {"key": "plz", "value": region_info[region]["plz"]},
            {"key": "demand", "value": region_info[region]["demand"]},
        ]
        if region in hub_plzs:
            metadata.extend(
                [
                    {"key": "capacity", "value": hub_info[region]["capacity"]},
                    {"key": "hub_id", "value": hub_info[region]["id"]},
                    {"key": "hub_name", "value": hub_info[region]["name"]},
                ]
            )
        region_polygon["properties"]["metadata"] = metadata

    # Remove regions that are not in the solution
    solution_regions = set(solution["assignments"].keys())
    for region in list(geojson["features"]):
        if region["properties"]["plz"] not in solution_regions:
            geojson["features"].remove(region)

    # Set the ID for each feature
    for region in geojson["features"]:
        region["id"] = region["properties"]["plz"]


def create_utilization_plot(
    result: dict,
) -> dict:
    """Creates a bar plot of the hub utilization."""
    # Convert demand to suitable dataframe
    solution = result["solution"]
    region_info = {region["plz"]: region for region in solution["regions"]}
    hub_capacity = {hub["id"]: hub["capacity"] for hub in solution["hubs"]}
    hub_demands = {hub["id"]: 0 for hub in solution["hubs"]}
    for region, hub in solution["assignments"].items():
        hub_demands[hub] += region_info[region]["demand"]

    # Create a plot of the hub utilization
    df = pd.DataFrame(
        [
            {"hub": hub, "utilization": hub_demands[hub] / hub_capacity[hub]}
            for hub in hub_demands.keys()
            if hub_capacity[hub] > 0
        ]
    )
    fig = plotly.express.bar(
        df,
        x="hub",
        y="utilization",
        color="hub",
    )
    fig.update_layout(
        title="Hub Utilization",
        xaxis_title="Hub",
        yaxis_title="Utilization",
        height=900,  # Set explicit height to make sure the plot is not too small
    )
    return json.loads(fig.to_json())


if __name__ == "__main__":
    main()
