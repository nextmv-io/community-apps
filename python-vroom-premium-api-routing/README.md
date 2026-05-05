# Verso Routing App

Simple example for running a Python application on the Nextmv Platform.

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

## Features

* Route optimization using Nextmv's Python SDK
* Interactive GeoJSON visualization with:
  * Color-coded routes for different vehicles
  * Step markers with detailed metadata (ID, distance, timing)
  * Route paths following actual road network
  * Leaflet-compatible GeoJSON output

## Visualization Details

The visualization includes:

* Route paths
* Step markers showing:
  * Vehicle assignment
  * Stop type and description
  * Stop ID
  * Distance and timing information
* Color differentiation between vehicle routes
* Interactive metadata on hover/click

## Next steps

* Open `main.py` and start writing the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
