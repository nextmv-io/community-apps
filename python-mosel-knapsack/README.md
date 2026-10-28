# Nextmv Python Mosel Knapsack

Example for running a Python application on the Nextmv Platform using a
[FICO Xpress Mosel][mosel] model and the Xpress community license. We solve a
knapsack Mixed Integer Programming problem.

The Mosel model (`knapsack.mos`) is bundled with the app. `main.py` reads the
JSON input, passes the data to the model and writes the solution. The options
of the app are defined in the `app.yaml`:

- Model options (e.g., `capacity`, `max_items`) are passed to the model as
  Mosel parameters (upper-cased, e.g., `max_items` sets `MAX_ITEMS`).
- Options prefixed with `xprs_` are passed to the solver as Xpress controls
  (e.g., `xprs_miprelstop` sets `XPRS_MIPRELSTOP`).

1. Install packages.

   - With `pip`

      ```bash
      pip install -r requirements.txt
      ```

   - With `uv`

      ```bash
      uv sync
      ```

1. Run the app.

   - With `python`

      ```bash
      cat input.json | python main.py
      ```

   - With `uv`

      ```bash
      cat input.json | uv run main.py
      ```

      Or with custom options:

      ```bash
      cat input.json | uv run main.py -capacity 30 -max_items 4
      ```

## Solver options

The `app.yaml` lists common Xpress controls as options, so that they show up
in the [Nextmv Console][console]. Any other Xpress control can be passed the
same way (e.g., `-xprs_feastol 1e-7`), even if it's not listed.

## Next steps

- Open `knapsack.mos` and modify the model. Add new parameters to the
  `app.yaml` to expose them as options.
- Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[mosel]: https://www.fico.com/fico-xpress-optimization/docs/latest/mosel/mosel_lang/dhtml/moselreflang.html
[docs]: https://docs.nextmv.io
[console]: https://cloud.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
