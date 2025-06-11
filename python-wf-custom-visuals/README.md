# Basic Workflow App

This example 

## Prerequisites

This example uses the _Nextmv Routing Marketplace App_. To run this example, do
the following:

1. Subscribe to the _Nextmv Routing Marketplace App_ in the [Nextmv console][console].
    - Set the App ID to `routing-nextroute`.
1. Create a **workflow** app in the [Nextmv console][console]. Note that this
   needs to specifically be a _workflow_ app. Note the App ID, it is referenced
   as `<app-id>` in the commands below.
1. Create a secrets collection in your new app via [console][console] and add
   your `NEXTMV_API_KEY` as an environment variable to it. Note the
   collection ID, it is referenced as `<secrets-collection-id>` in the commands
   below.
1. Install the [Nextmv CLI][cli] if you haven't done so already.

## Run the workflow locally

It is possible to run (and debug) the workflow locally. To do this, you need to
have supported Python version installed, as well as export the `NEXTMV_API_KEY`
environment variable with your Nextmv API key.

```bash
export NEXTMV_API_KEY=<your-nextmv-api-key>
cat input.json | python3 main.py
```

## Run the workflow remotely

For running the workflow remotely, we need to first push the app. Then, we can
make a remote run using the Nextmv CLI (alternatively, you can make a run using
the [Nextmv console][console]).

```bash
nextmv app push -a <app-id>
nextmv app run -a <app-id> --input input.json -s <secrets-collection-id>
```

## Sneak peek

When you run the workflow, it will attach the custom visual asset to the run.
You can see these in [console][console] for example. Here is a sneak peek of
them.

Routes plotted as clusters:

![sneak peek clusters](https://nextmv-io.github.io/community-apps/content/apps/python-wf-custom-visuals/clusters.png)

## Next steps

- Modify the workflow in `main.py` to suit your needs.
- Visit our [general docs][docs], [workflow docs][workflow] and [blog][blog].
  Need more assistance? [Contact][contact] us!

[console]: https://cloud.nextmv.io
[docs]: https://docs.nextmv.io
[workflow]: https://nextpipe.readthedocs.io/en/latest/
[cli]: https://docs.nextmv.io/docs/using-nextmv/setup/install#nextmv-cli
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
