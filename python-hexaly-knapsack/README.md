# Nextmv Python Hexaly Knapsack

Example for running a Python application on the Nextmv Platform using the
Hexaly solver. We solve a knapsack Mixed Integer Programming problem.

If you have a Hexaly license, remove the `.template` extension from the
`license.dat.template` file and replace the contents with your actual license
key. Modify the `app.yaml` file to include the `license.dat` in the files list.

1. Install packages.

   * With `pip`

      ```bash
      pip install -r requirements.txt
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
      cat input.json | uv run main.py -duration 30
      ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

<!-- markdownlint-disable MD013 -->
```bash
docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'pip install -r /app/requirements.txt && python3 /app/main.py -input input.json -output output.json -duration 30'
```
<!-- markdownlint-enable MD013 -->

You can also debug the application by running it in a container by
using the command `Dev Containers: Reopen in Container`.

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
