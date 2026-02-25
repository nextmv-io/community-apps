# Nextmv Python Xpress Facility Location

Example for running a Python application on the Nextmv Platform using the
FICO Xpress package. We solve a facility location problem using Bender’s
Decomposition. The facility location problem is a common type of optimization
problem in distribution and logistics. It involves determining the best (i.e.,
cost-minimizing) locations to set up facilities like warehouses or factories to
minimize the cost of serving a set of customers.

The cost of supplying a product to each region includes the cost of waste
(unsold products) and the cost of transport.

Given a set of potential facility locations and a set of customers, the goal is
to decide where to open facilities and how to serve the customers from those
facilities such that the total cost is minimized. The total cost includes the
fixed costs of opening facilities, the variable costs of serving customers from
those facilities, and the capacity constraints of each facility.

The Xpress community edition is in variables and constraints. For larger
problems, a commercial license is required.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

2. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
