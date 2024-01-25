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

1. Make sure that all the required packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

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
