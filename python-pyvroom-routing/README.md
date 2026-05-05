# Nextmv Python Pyvroom Routing

Example for running a Python application on the Nextmv Platform using the
Pyvroom package. We solve a vehicle routing problem.

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

      Or with custom options:

      ```bash
      cat input.json | uv run main.py \
         -duration 30 -exploration_level 4 -threads 6
      ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:latest \
sh -c 'pip install -r requirements.txt > /dev/null && python3 /app/main.py'
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by
using the command `Dev Containers: Reopen in Container`.

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
