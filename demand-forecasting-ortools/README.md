# Demand forecasting with OR-Tools

This is an example of how to use [OR-Tools][or-tools] to solve a demand
forecasting problem. The goal is to use historical demands by time to
forecast a given demand in the future.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a Least Absolute Deviation (LAD) Regression to forecast
  demand.
* `input.json` is a sample input file.

## Usage

Follow these steps to run locally.

1. The packages listed in the `requirements.txt` file are available when using
   the runtime specified in the `app.yaml` manifest. This runtime is used when
   making remote runs. When working locally, make sure that all the required
   packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

1. A file `output.json` should have been created with a solution to the demand
   forecasting problem.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/ortools:latest \
python3 /app/main.py
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

[or-tools]: https://developers.google.com/optimization
