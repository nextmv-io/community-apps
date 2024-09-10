# Nextmv Python PyOptInterface Knapsack

Example for running a Python application on the Nextmv Platform using the
PyOptInterface package. We solve a knapsack Mixed Integer Programming problem.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/pyomo:latest \
sh -c 'python3 /app/main.py'
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
