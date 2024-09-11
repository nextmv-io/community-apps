# Nextmv Python AMPL Price Optimization

Example for running a Python application on the Nextmv Platform using the AMPL
package. We solve a price optimization Mixed Integer Problem (MIP). This app is
inspired by the [Avocado Price Optimization][gurobi-blog] blog post published
by Gurobi.

We aim to optimize both the price and quantity (in millions) of
a product shipped to a set of regions. The revenue in each region is determined
by the sales volume and the price of the product. The sales volume is influenced
by the price and it cannot exceed the quantity of the product supplied to the
region.

The cost of supplying a product to each region includes the cost of waste
(unsold products) and the cost of transport.

Given a set of regions, a total supply of product, minimum / maxium product
allocations and prices per region, costs to transport products and costs for
wasted products, and regression coefficients for a model correlating price to
expected demand, we determine the following:

* `price` (price of the product in each region)
* `quantity` (quantity of the product supplied to each region)

While maximizing expected profit (`revenue - cost`).

If you have an AMPL license, remove the `.template` extension from the
`ampl_license_uuid.template` file and replace the contents with your actual
license key. Modify the `app.yaml` file to include the `ampl_license_uuid` in
the files list.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json \
      -duration 30 -provider highs -model .
    ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

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

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

## Notes

This model rounds off some variables for simplicity. We recommend users handle
data types explicitly when working with this model.

[gurobi-blog]: https://www.google.com/search?q=gurobi+price+optimization+avocado&rlz=1C5CHFA_enUS904US904&oq=gurobi+price+optimization+avocado&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQRRg80gEINDU2MGowajSoAgCwAgE&sourceid=chrome&ie=UTF-8
[docs]: <https://docs.nextmv.io>
[blog]: <https://www.nextmv.io/blog>
[contact]: <https://www.nextmv.io/contact>
