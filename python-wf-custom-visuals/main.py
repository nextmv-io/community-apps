import colorsys

import nextmv
from nextpipe import FlowSpec, app, needs, step
from scipy.spatial import ConvexHull

POLYGON_URL = "https://gist.githubusercontent.com/merschformann/74f34f9b9cd21b624586035dfe015ec5/raw/952b0f6574713d7c7e79638bee46aa6918bcc35d/plz-filtered.geojson"


# >>> Workflow definition
class Flow(FlowSpec):
    @step
    def prepare(input_data: dict):
        """Prepares the input data."""
        return input_data

    @app(
        app_id="routing-nextroute",  # ID of any app on your team.
        instance_id="latest",  # Use "latest" for marketplace instances.
        parameters={
            "model.constraints.enable.cluster": True,  # Enable clustering of routes.
            "solve.duration": 5,  # 5 seconds time limit for solving.
        },
    )
    @step
    def solve():
        """Solves the routing problem using Nextroute Marketplace App."""
        pass  # Execution happens in sub-app.

    @needs(predecessors=[solve])
    @step
    def postprocess(result: dict):
        """Post-processes the result."""

        # Add custom cluster polygon visualization of the routes via geojson.
        geojson = {}
        if "solutions" in result and result["solutions"]:
            polygons = [
                (
                    convex_hull_scipy(vehicle["route"]),
                    vehicle["id"],
                    vehicle["route_duration"],
                    vehicle["route_travel_duration"],
                    vehicle["route_travel_distance"],
                )
                for vehicle in result["solutions"][-1]["vehicles"]
            ]
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [polygon],
                        },
                        "properties": {
                            "name": f"Route {i + 1}",
                            "style": {
                                "color": get_color(i / len(polygons)),
                                "fillColor": get_color(i / len(polygons)),
                                "fillOpacity": 0.8,
                            },
                            "metadata": [
                                {"key": "Vehicle ID", "value": vehicle_id},
                                {"key": "#Stops", "value": len(polygon) - 1},  # Exclude the closing point
                                {"key": "Route Duration", "value": f"{duration:.2f} seconds"},
                                {"key": "Travel Duration", "value": f"{travel_duration:.2f} seconds"},
                                {"key": "Travel Distance", "value": f"{travel_distance:.2f} meters"},
                            ],
                        },
                    }
                    for i, (polygon, vehicle_id, duration, travel_duration, travel_distance) in enumerate(polygons)
                ],
            }

        # Write out the result
        return nextmv.Output(
            json_configurations={
                "indent": None,
                "separators": (",", ":"),
            },
            solution=result["solutions"][-1],
            statistics=result["statistics"],
            assets=[
                nextmv.Asset(
                    name="clusters",
                    content_type="json",
                    visual=nextmv.Visual(
                        visual_schema=nextmv.VisualSchema(value=nextmv.VisualSchema.GEOJSON),
                        label="Clusters",
                        visual_type="custom-tab",
                    ),
                    content=geojson,
                ),
            ],
        )


def main():
    """
    Main function to run above workflow.
    """
    # Load input data
    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
    )
    input = nextmv.load(options=options, path=options.input)

    # Run workflow
    flow = Flow("DecisionFlow", input.data)
    flow.run()

    # Write out the result
    nextmv.write(output=flow.get_result(flow.postprocess), path=options.output)


def convex_hull_scipy(route: list[dict]) -> list[tuple[float, float]]:
    """
    Helper function that computes the convex hull of a set of points using scipy's
    ConvexHull.
    """
    points = [(point["stop"]["location"]["lon"], point["stop"]["location"]["lat"]) for point in route]
    polygon = [tuple(points[i]) for i in ConvexHull(points).vertices]
    polygon.append(polygon[0])  # Close the polygon
    return polygon


def get_color(value: float) -> str:
    """
    Helper function to convert a percentage value to a color in hex format.
    """
    r, g, b = colorsys.hsv_to_rgb(value, 0.8, 0.8)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


if __name__ == "__main__":
    main()
