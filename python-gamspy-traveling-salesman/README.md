# Nextmv GAMSPy Traveling Salesman Problem

Example for running a Python application on the Nextmv Platform using
[GAMSPy](https://gamspy.readthedocs.io/en/latest/) to model the problem. We
solve the traveling salesman problem that minimizes the total distance traveled
while visiting each city exactly once.

1. Install packages.

   * With `pip`

      ```bash
      pip install .
      ```

   * With `uv`
  
      ```bash
      uv sync
      ```

2. Run the app.

   * With `python`

      ```bash
      cat data.json | python main.py
      ```

   * With `uv`

      ```bash
      cat data.json | uv run main.py
      ```

      Or with custom options:

      ```bash
      cat data.json | uv run main.py -maxnodes 10
      ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
