# Nextmv Pyomo Python template

This template demonstrates how to solve a Mixed Integer Programming problem
using the open source software suite [Pyomo][pyomo].

To solve a Mixed Integer Problem (MIP) is to optimize a linear objective
function of many variables, subject to linear constraints. We demonstrate this
by solving the knapsack problem using the [Python interface][pyomo-docs].

Knapsack is a classic combinatorial optimization problem. Given a collection of
items with a value and weight, our objective is to maximize the total value
without exceeding the weight capacity of the knapsack.

The input defines a number of items which have an id to identify the item, a
weight and a value. Additionally there is a weight capacity.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a MIP knapsack solver.
* `input.json` is a sample input file.

Follow these steps to run locally.

1. The packages listed in the `requirements.txt` file are available when using
   the runtime specified in the `app.yaml` manifest. This runtime is used when
   making remote runs. When working locally, make sure that all the required
   packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

1. Further dependencies can be specified in the `requirements_extra.txt` file.
   These dependencies will get bundled with the app on push.

1. Pyomo [does not include any solvers][pyomo-solvers]. This template assumes
   that supported providers are [`glpk`][glpk] and [`cbc`][cbc]. Make sure you
   have installed them locally, as they are already installed on the image when
   running remotely. Please [contact support][support] if you need a different
   solver.

1. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json \
      -duration 30 -provider cbc
    ```

1. A file `output.json` should have been created with the optimal knapsack
   solution.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/pyomo:latest \
sh -c 'python3 /app/main.py'
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## Next steps

* Open `main.py` and read through the comments to understand the model.
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!

[pyomo]: http://www.pyomo.org
[pyomo-docs]: https://pyomo.readthedocs.io/en/stable/index.html
[pyomo-solvers]: http://www.pyomo.org/installation
[glpk]: https://www.gnu.org/software/glpk/
[cbc]: https://projects.coin-or.org/Cbc
[support]: https://www.nextmv.io/contact
