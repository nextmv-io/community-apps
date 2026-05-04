# Nextmv Workflow for generating visual assets for the Region Allocation app

This example shows how to wrap the Region Allocation app in a meta-app using
workflows in order to add additional visual assets to its runs.

## Prerequisites

This example assumes that you already have pushed the [Region Allocation][region-allocation]
app to the Nextmv platform (below steps use [Nextmv CLI][cli] to push the app -
refer to docs for alternative methods).:

1. Create a new custom app in the Nextmv platform with the ID
   `region-allocation`.
1. Change to the directory of the app.

    ```bash
    cd ../python-ortools-region-allocation
    ```

1. Push the app to the Nextmv platform.

    ```bash
    nextmv app push -a region-allocation
    ```

## Push example to Nextmv platform and run it

1. Install packages.

   * With `pip`

      ```bash
      pip install .
      ```

   * With `uv`
  
      ```bash
      uv sync
      ```

2. Run the app.

   * With `python`

      ```bash
      cat input.json | python main.py
      ```

   * With `uv`

      ```bash
      cat input.json | uv run main.py
      ```

## Sneak peek

When you run the workflow, it will attach the visual assets to the run. You can
see these in [console][console] for example. Here is a sneak peek of them.

Demand of the regions visualized as a choropleth map:

![sneak peek demand](https://nextmv-io.github.io/community-apps/apps/python-wf-ortools-region-allocation/demand.png)

Allocation of the regions to the hubs visualized as a map:

![sneak peek allocation](https://nextmv-io.github.io/community-apps/apps/python-wf-ortools-region-allocation/allocation.png)

## Next steps

* Add run tracking to your own code.
* Visit our [general docs][docs], [workflow docs][workflow] and [blog][blog].
  Need more assistance? [Contact][contact] us!

[region-allocation]: ../python-ortools-region-allocation
[console]: https://cloud.nextmv.io
[docs]: https://docs.nextmv.io
[workflow]: https://nextpipe.readthedocs.io/en/latest/
[cli]: https://docs.nextmv.io/docs/using-nextmv/setup/install#nextmv-cli
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
