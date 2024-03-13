# Nextmv AMPL Python template

This template demonstrates how to solve a Mixed Integer Programming problem
using the AMPL Python package [amplpy][amplpy].

To solve a Mixed Integer Problem (MIP) is to optimize a linear objective
function of many variables, subject to linear constraints. We demonstrate this
by solving the knapsack problem.

Knapsack is a classic combinatorial optimization problem. Given a collection of
items with a value and weight, our objective is to maximize the total value
without exceeding the weight capacity of the knapsack.

The input defines a number of items which have an id to identify the item, a
weight and a value. Additionally there is a weight capacity.

The most important files created are `main.py`, `input.json`, and
`ampl_license_uuid.template`.

* `main.py` implements a MIP knapsack solver.
* `input.json` is a sample input file.
* `ampl_license_uuid.template` is a file demonstrating how to use the AMPL UUID
  license key.
  * If you have an AMPL license, remove the `.template` extension and replace
    the contents with your actual license key to be left with a file named
    `ampl_license_uuid`. Modify the `app.yaml` file to include the
    `ampl_license_uuid` in the files list.
  * If you are just testing and don’t have an AMPL license, you don’t need to
    do anything, as this community app ships with a special license that allows
    you to test AMPL with limits per AMPL's website.

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
    python3 main.py -input input.json -output output.json \
      -duration 30 -provider cbc
    ```

3. A file `output.json` should have been created with the optimal knapsack
   solution.

## Next steps

* Open `main.py` and read through the comments to understand the model.
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!

[amplpy]: https://amplpy.ampl.com/en/latest/?_gl=1*16ca5pw*_ga*Nzk4OTUwMDgwLjE3MDgzNTIzMzg.*_ga_FY84K2YRRE*MTcwODQ0NTgwMy42LjEuMTcwODQ0NTgzOC4wLjAuMA..
