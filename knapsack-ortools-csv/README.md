# Nextmv OR-Tools Python template with CSV in/out

This template demonstrates how to solve a Mixed Integer Programming problem
using the open source software suite [OR-Tools][or-tools] and using CSV for
inputs and outputs.

To solve a Mixed Integer Problem (MIP) is to optimize a linear objective
function of many variables, subject to linear constraints. We demonstrate this
by solving the knapsack problem using the [integer
optimzation][integer-optimization] interface.

Knapsack is a classic combinatorial optimization problem. Given a collection of
items with a value and weight, our objective is to maximize the total value
without exceeding the weight capacity of the knapsack.

The `input` folder defines the inputs of the problem:

- `items.csv` contains the items to be considered in the knapsack problem.
- `weight_capacity.csv` contains the weight capacity of the knapsack.

The  `main.py` file implements a MIP knapsack solver. The code is configured to
work with Nextmv Cloud and fulfills these requirements:

- It reads the necessary input files from the `input` folder.
- Writes the solution file(s) to an `output` folder.
- Streams the statistics of the solution to `stdout`.

Follow these steps to run locally.

1. The packages listed in the `requirements.txt` file are available when using
   the runtime specified in the `app.yaml` manifest. This runtime is used when
   making remote runs. When working locally, make sure that all the required
   packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

2. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -duration 30
    ```

3. An `output` directory should have been created with the optimal knapsack
   solution in the `solution.csv` file.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'pip install -r requirements.txt && python3 /app/main.py'
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## Next steps

- Open `main.py` and read through the comments to understand the model.
- Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
- Need more assistance? Send us an [email](mailto:support@nextmv.io)!

[or-tools]: https://developers.google.com/optimization
[integer-optimization]: https://developers.google.com/optimization/mip
