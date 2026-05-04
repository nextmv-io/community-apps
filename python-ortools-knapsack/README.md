# Nextmv Python OR-Tools Knapsack

Example for running a Python application on the Nextmv Platform using the
OR-Tools package. We solve a knapsack Mixed Integer Programming problem.

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
      cat inputs/input.json | python main.py
      ```

   * With `uv`

      ```bash
      cat inputs/input.json | uv run main.py
      ```

      Or with custom options:

      ```bash
      cat inputs/input.json | uv run main.py -duration 30 -provider SCIP
      ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
