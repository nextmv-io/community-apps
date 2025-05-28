# Nextmv Tracked Runs for OR-Tools Region Allocation

This example shows how to use Nextmv Tracked Runs feature to track runs of an
OR-Tools region allocation MIP model.

> [!NOTE]  
> This is an external example, so, pushing this model to Nextmv platform is not
> part of the example. See [python-wf-ortools-region-allocation](../python-wf-ortools-region-allocation)
> for a complete 'nextmvified' example.

The example is intentionally not using any Nextmv features apart from the run
tracking. This is to better show that tracking runs can be easily added to
existing code. Find the `POST TRACKED RUN TO NEXTMV PLATFORM` comment in
`main.py` to see where the tracked run is created.

## Problem description

This model solves the region to hub allocation problem. I.e., given a set of
regions with certain demands and a set of hubs with certain capacities, the goal
is to assign each region to a hub such that the total demand of the regions
assigned to a hub does not exceed the hub's capacity. The objective is to
keep the regions as close to their assigned hub as possible.

## Run the example

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Create an app on the [Nextmv platform][platform] (if you haven't already) and
   get your API key and app ID.

1. Set up your environment.

    ```bash
    export NEXTMV_API_KEY=your_api_key
    export NEXTMV_APP_ID=your_app_id
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json
    ```

## Next steps

* Add run tracking to your own code.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[platform]: https://cloud.nextmv.io
[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
