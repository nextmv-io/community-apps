# Nextmv AMPL Price Optimization App

This app demonstrates how to solve a Price Optimization Mixed Integer Problem
(MIP) using the AMPL Python package [amplpy][amplpy]. We were inspired by the
[Avocado Price Optimization][gurobi-blog]] blog post published by Gurobi.

In this problem, we aim to optimize both the price and quantity of a product
shipped to a set of regions. The revenue in each region is determined by the
sales volume and the price of the product. The sales volume is influenced by the
price and it cannot exceed the quantity of the product supplied to the region.

The cost of supplying a product to each region includes the cost of waste
(unsold products) and the cost of transport.

Given a set of regions, a total supply of product, minimum / maxium product
allocations and prices per region, costs to transport products and costs for
wasted products, and regression coefficients for a model correlating price to
expected demand, we determine the following:

* `price` (price of the product in each region)
* `quantity` (quantity of the product supplied to each region)

While maximizing expected profit (`revenue - cost`).

The most important files created are `main.py`, `ampl_model.mod`, `input.json`,
and `ampl_license_uuid.template`.

* `main.py` invokes AMPL to solve the price optimization problem
* `ampl_model.mod` defines the model to solve the price optimization problem
* `input.json` is a sample input file.
* `ampl_license_uuid.template` is a file demonstrating how to use the AMPL UUID
  license key.
  * If you have an AMPL license, remove the `.template` extension and replace
    the contents with your actual license key to be left with a file named
    `ampl_license_uuid`. Modify the `app.yaml` file to include the
    `ampl_license_uuid` in the files list. Note: when running on Nextmv Cloud,
    you should use a premium execution class to use your own AMPL license.
  * If you are just testing and don’t have an AMPL license, you don’t need to
    do anything, as this community app ships with logic that allows you to test
    AMPL with limits per AMPL’s website.

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
      -duration 30 -provider highs
    ```

3. A file `output.json` should have been created with the optimal knapsack
   solution.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/ampl:latest \
python3 /app/main.py
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

[amplpy]: https://amplpy.ampl.com/en/latest/?_gl=1*16ca5pw*_ga*Nzk4OTUwMDgwLjE3MDgzNTIzMzg.*_ga_FY84K2YRRE*MTcwODQ0NTgwMy42LjEuMTcwODQ0NTgzOC4wLjAuMA..
[gurobi-blog]: https://www.google.com/search?q=gurobi+price+optimization+avocado&rlz=1C5CHFA_enUS904US904&oq=gurobi+price+optimization+avocado&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQRRg80gEINDU2MGowajSoAgCwAgE&sourceid=chrome&ie=UTF-8
