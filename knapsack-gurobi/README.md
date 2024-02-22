# Nextmv Gurobi template

This template demonstrates how to solve a Mixed Integer Programming problem
using [Gurobi][gurobi].

To solve a Mixed Integer Problem (MIP) is to optimize a linear objective
function of many variables, subject to linear constraints. We demonstrate this
by solving the knapsack problem.

Knapsack is a classic combinatorial optimization problem. Given a collection of
items with a value and weight, our objective is to maximize the total value
without exceeding the weight capacity of the knapsack.

The input defines a number of items which have an id to identify the item, a
weight and a value. Additionally there is a weight capacity.

The most important files created are `main.py`, `input.json`, and
`gurobi.lic.template`.

* `main.py` implements a MIP knapsack solver.
* `input.json` is a sample input file.
* `gurobi.lic.template` is a file demonstrating how to use the Gurobi WSL
  license. Remove the `.template` extension and replace the contents with your
  actual values to be left with a file named `gurobi.lic`.

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

1. A file `output.json` should have been created with the optimal knapsack
   solution.

## Next steps

* Open `main.py` and read through the comments to understand the model.
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!

[gurobi]: https://www.gurobi.com
