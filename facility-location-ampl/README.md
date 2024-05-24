# Nextmv AMPL Facility Location App

This app demonstrates how to solve a facility location problem using Bender's
Decomposition with the AMPL Python package [amplpy][amplpy]. The facility
location problem is a common type of optimization problem in distribution and
logistics. It involves determining the best (i.e., cost-minimizing) locations to
set up facilities like warehouses or factories to minimize the cost of serving a
set of customers.

The cost of supplying a product to each region includes the cost of waste
(unsold products) and the cost of transport.

Given a set of potential facility locations and a set of customers, the goal is
to decide where to open facilities and how to serve the customers from those
facilities such that the total cost is minimized. The total cost includes the
fixed costs of opening facilities, the variable costs of serving customers from
those facilities, and the capacity constraints of each facility.

The input data is provided in a JSON file with the following keys:

* `FACILITIES:` A list of potential facility locations.
* `CUSTOMERS:` A list of customers to be served.
* `SCENARIOS:` A list of scenarios. Each scenario represents a different set of
customer demands.
* `prob:` A dictionary mapping each scenario to its probability.
* `fixed_cost:` A JSON string representing a DataFrame with the fixed cost of
opening each facility.
* `facility_capacity:` A JSON string representing a DataFrame with the capacity
  of each facility.
* `variable_cost:` A JSON string representing a DataFrame with the variable cost
of serving each customer from each facility.
* `customer_demand:` A JSON string representing a DataFrame with the demand of
  each customer in each scenario.

The output of the program is a set of decisions indicating which facilities to
open and how to serve each customer from those facilities in each scenario.

The most important files created are `main.py`, `floc_bend.mod`,
`floc_bend.run`, `input.json`, and `ampl_license_uuid.template`.

* `main.py` invokes AMPL to solve the facility location problem.
* `floc_bend.mod` defines the AMPL model.
* `floc_bend.run` contains commands executed by the AMPL interpreter.
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

1. The packages listed in the `requirements.txt` will get bundled with the app
   as defined in the `app.yaml` manifest. When working locally, make sure that
   these are installed as well:

    ```bash
    pip3 install -r requirements.txt
    ```

2. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json \
      -duration 30 -provider highs -modelpath . -runpath .
    ```

3. A file `output.json` should have been created with the optimal facility
   location solution.

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

## Next steps

* Open `main.py` and read through the comments to understand the model.
* Further documentation, guides, and API references about custom modeling and
  deployment can also be found on our [blog](https://www.nextmv.io/blog) and on
  our [documentation site](https://docs.nextmv.io).
* Need more assistance? Send us an [email](mailto:support@nextmv.io)!

## Notes

We acknowledge there are outdated terms used in the comments of this
application. We will be looking to update those with more appropriate language
going forward. We prefer talking about an “outer” problem vs a “master” problem,
but this is not a widely used alternative in the context of this space at the
time of writing this.

[amplpy]: https://amplpy.ampl.com/en/latest/?_gl=1*16ca5pw*_ga*Nzk4OTUwMDgwLjE3MDgzNTIzMzg.*_ga_FY84K2YRRE*MTcwODQ0NTgwMy42LjEuMTcwODQ0NTgzOC4wLjAuMA..
