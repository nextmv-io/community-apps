# Shift planning with OR-Tools

This is an example of how to use [OR-Tools][or-tools] to solve a shift planning
problem. The goal is to select/plan a number of shifts according to a given
demand and qualification that will later be filled by employees.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a MIP shift planning solver.
* `input.json` is a sample input file.

## Usage

Follow these steps to run locally.

1. The packages listed in the `requirements.txt` will get bundled with the app
   as defined in the `app.yaml` manifest. When working locally, make sure that
   these are installed as well:

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

1. A file `output.json` should have been created with a solution to the shift
   planning problem.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'pip install -r requirements.txt > /dev/null && python3 /app/main.py'
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

[or-tools]: https://developers.google.com/optimization
