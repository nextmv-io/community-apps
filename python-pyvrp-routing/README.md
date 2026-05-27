# Nextmv Python PyVRP Routing

Example for running a Python application on the Nextmv Platform using the
PyVRP package. We solve a vehicle routing problem.

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
      cat input.json | python main.py -duration 5
      ```

   * With `uv`

      ```bash
      cat input.json | uv run main.py -duration 5
      ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
