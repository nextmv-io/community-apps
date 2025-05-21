# Nextmv Tracked Runs for OR-Tools Region Allocation

This example shows how to wrap the Region Allocation app in a meta-app using
workflows in order to add additional visual assets to its runs.

## Prerequisites

This example assumes that you already have pushed the [Region Allocation][region-allocation]
app to the Nextmv platform (below steps use [Nextmv CLI][cli] to push the app - refer
to docs for alternative methods).:

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

1. Switch to the directory of this example (if still in the previous directory).

    ```bash
    cd ../python-wf-ortools-region-allocation
    ```

1. Create a new _**workflow**_ app in the Nextmv platform with the ID
   `region-allocation-workflow`.
1. Push the workflow to the Nextmv platform.

    ```bash
    nextmv app push -a region-allocation-workflow
    ```

1. Create a version of the code that was just pushed.

    ```bash
    nextmv app version create -a region-allocation-workflow -v v1.0.0 -n v1.0.0
    ```

1. Create a new instance using the version.

    ```bash
    nextmv app instance create -a region-allocation-workflow -v v1.0.0 -i main -n "Main Instance"
    ```

1. Create a secrets collection via [console][console] and add your
   `NEXTMV_API_KEY` as an environment variable to it.
1. Assign the secrets collection to the instance you created in the previous
   step.

1. Make a run.

    ```bash
    nextmv app run -a region-allocation-workflow --instance-id main --input input.json
    ```

## Sneak peek

When you run the workflow, it will attach the visual assets to the run. You can
see these in [console][console] for example. Here is a sneak peek of them.

Demand of the regions visualized as a choropleth map:

![sneak peek demand](https://nextmv-io.github.io/community-apps/content/apps/python-wf-ortools-region-allocation/demand.png)

Allocation of the regions to the hubs visualized as a map:

![sneak peek allocation](https://nextmv-io.github.io/community-apps/content/apps/python-wf-ortools-region-allocation/allocation.png)

## Next steps

* Add run tracking to your own code.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[region-allocation]: ../python-ortools-region-allocation
[console]: https://cloud.nextmv.io
[docs]: https://docs.nextmv.io
[cli]: https://docs.nextmv.io/docs/using-nextmv/setup/install#nextmv-cli
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
