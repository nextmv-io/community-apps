# Shift planning with OR-Tools

This is an example of how to use [OR-Tools][or-tools] to solve a shift planning
problem. The goal is to select/plan a number of shifts according to a given
demand and qualification that will later be filled by employees.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a MIP shift planning solver.
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

1. A file `output.json` should have been created with a solution to the shift
planning problem.

[or-tools]: https://developers.google.com/optimization
