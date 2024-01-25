# Shift assignment with Pyomo

This app solves a shift asssignment problem using [Pyomo][pyomo]. Given a
set of previously planned shifts, in this app we assign workers to those shifts,
taking different factors into account such as availability and qualification.

The most important files created are `main.py` and `input.json`.

* `main.py` implements a MIP shift assignment solver.
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
assignment problem.

[pyomo]: http://www.pyomo.org/
