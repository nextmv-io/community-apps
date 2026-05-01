# cuOpt Routing App

Simple example for solving a routing model using NVIDIA's [cuOpt][cuopt] on
Nextmv.

To run the model locally, you must have a cuOpt-capable NVIDIA GPU. Open the
[dev container][devcontainer] in the project and run:

1. Install packages.

   * With `pip`

      ```bash
      pip install .
      ```

2. Run the app.

   * With `python`

      ```bash
      cat input.json | python main.py
      ```

      Or with custom options:

      ```bash
      cat input.json | python main.py -time_limit 5
      ```

## Features

* Route optimization using Nextmv's Python SDK
* Interactive GeoJSON visualization
* Development container for local execution

## Next steps

* Open `main.py` and start writing the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
[cuopt]: https://www.nvidia.com/en-us/ai-data-science/products/cuopt/
[devcontainer]: https://containers.dev/
[docs]: https://docs.nextmv.io
