# Nextmv Python AMPL Facility Location

Example for running a Python application on the Nextmv Platform using the AMPL
package. We solve a facility location problem using Bender’s Decomposition. The
facility location problem is a common type of optimization problem in
distribution and logistics. It involves determining the best (i.e.,
cost-minimizing) locations to set up facilities like warehouses or factories to
minimize the cost of serving a set of customers.

The cost of supplying a product to each region includes the cost of waste
(unsold products) and the cost of transport.

Given a set of potential facility locations and a set of customers, the goal is
to decide where to open facilities and how to serve the customers from those
facilities such that the total cost is minimized. The total cost includes the
fixed costs of opening facilities, the variable costs of serving customers from
those facilities, and the capacity constraints of each facility.

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
      -duration 30 -provider highs -modelpath . -runpath .
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

We acknowledge there are outdated terms used in the comments of this
application. We will be looking to update those with more appropriate language
going forward. We prefer talking about an “outer” problem vs a “master” problem,
but this is not a widely used alternative in the context of this space at the
time of writing this.

[docs]: <https://docs.nextmv.io>
[blog]: <https://www.nextmv.io/blog>
[contact]: <https://www.nextmv.io/contact>
