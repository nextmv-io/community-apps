# Routing with OR-Tools

This app solves an unconstrained routing problem using [OR-Tools][or-tools].
Given a distance matrix (and with it indirectly the stops), a number of vehicles
and a depot.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a routing solver.
* `input.json` is a sample input file.

## Usage

Follow these steps to run locally.

1. Make sure that all the required packages are installed:

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the command below to check that everything works as expected:

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

1. A file `output.json` should have been created with a solution to the routing
problem.

[or-tools]: https://developers.google.com/optimization
