# Nextmv GAMS Cutstock Problem

Example for running a Python application on the Nextmv Platform using the GAMS
[control API](https://www.gams.com/latest/docs/API_PY_CONTROL.html). We solve a
cutting stock problem that finds the minimum number of cuts required to satisfy
the product demand.

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
      cat data.json | uv run main.py -raw_width 100 -max_pattern 35
      ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
