import asyncio
import datetime
import json

import nextmv
import nextroute.schema as nextrouteSchema
from nextpipe import FlowSpec, app, needs, step
from traveltimepy import Coordinates, Driving, Location, Property, TravelTimeSdk

# async def main():
#     sdk = TravelTimeSdk("YOUR_APP_ID", "YOUR_APP_KEY")

#     locations = [
#         Location(id="London center", coords=Coordinates(lat=51.508930, lng=-0.131387)),
#         Location(id="Hyde Park", coords=Coordinates(lat=51.508824, lng=-0.167093)),
#         Location(id="ZSL London Zoo", coords=Coordinates(lat=51.536067, lng=-0.153596))
#     ]

#     results = await sdk.time_filter_fast_async(
#         locations=locations,
#         search_ids={
#             "London center": ["Hyde Park", "ZSL London Zoo"],
#             "ZSL London Zoo": ["Hyde Park", "London center"],
#         },
#         transportation=Transportation(type="public_transport"),
#         one_to_many=False
#     )

#     print(results)

# asyncio.run(main())


# >>> Workflow definition
class Flow(FlowSpec):
    @step
    def get_durations_distances(input: nextrouteSchema.Input):
        """Get distances and durations from TravelTime."""

        locations = []
        for _, stop in input.stops:
            locations.append(
                Location(id=stop.id, coords=Coordinates(lat=stop.lat, lng=stop.lng))
            )
        sdk = TravelTimeSdk("YOUR_APP_ID", "YOUR_APP_KEY")

        search_ids = {}
        for _, stop in input.stops:
            search_ids[stop.id] = [s.id for s in input.stops]

        # TODO: make transportation type a config
        async def generate_matrix(size: int):
            sdk = TravelTimeSdk("APP_ID", "API_KEY")
            location_ids = [location.id for location in locations]

            return await sdk.time_filter_async(
                locations=locations,
                search_ids=dict(search_ids),
                properties=[Property("distance")],
                transportation=Driving(),
                arrival_time=datetime.now(),
            )

    def sync_func():
        async def wrapper():
            return await async_func()

        results = asyncio.run(wrapper())
        input["duration_matrix"] = results.get("durations", {})
        input["distance_matrix"] = results.get("distances", {})
        return input

    @app(app_id="nextroute")
    @needs(predecessors=[get_durations_distances])
    @step
    def solve():
        """Runs the model."""
        pass


def main():
    # Load input data
    input = nextmv.load_local()

    # Run workflow
    flow = Flow("DecisionFlow", input.data)
    flow.run()

    # Write out the result
    print(json.dumps(flow.get_result(flow.solve)))


if __name__ == "__main__":
    main()
