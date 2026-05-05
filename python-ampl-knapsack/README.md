# Nextmv Python AMPL Knapsack

Example for running a Python application on the Nextmv Platform using the AMPL
package. We solve a knapsack Mixed Integer Programming problem.

If you have an AMPL license, remove the `.template` extension from the
`ampl_license_uuid.template` file and replace the contents with your actual
license key. Modify the `app.yaml` file to include the `ampl_license_uuid` in
the files list.

1. Install packages.

   * With `pip`

      ```bash
      pip install -r requirements.txt
      ```

   * With `uv`
  
      ```bash
      uv sync
      ```

2. Run the app.

   * With `python`

      ```bash
      cat input.json | python main.py
      ```

   * With `uv`

      ```bash
      cat input.json | uv run main.py
      ```

      Or with custom options:

      ```bash
      cat input.json | uv run main.py -duration 30 -provider highs
      ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
