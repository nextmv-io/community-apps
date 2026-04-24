# Nextmv & Gurobi Price Optimization

This community app demonstrates avocado price and supply optimization using
Gurobi. The optimization model determines optimal pricing and supply allocation
across different regions to maximize revenue while minimizing waste and
transport costs.

The model uses regression coefficients to predict demand based on price, region,
year, and seasonality factors, then optimizes the supply and pricing strategy
accordingly.

If you have a Gurobi WSL license, remove the `.template` extension from the
`gurobi.lic.template` file and replace the contents with your actual license
key. Modify the `app.yaml` file to include the `gurobi.lic` in the files list.

## Running the app

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
      cat input.json | python main.py
      ```

   * With `uv`

      ```bash
      cat input.json | uv run main.py
      ```

      Or with custom options:

      ```bash
      cat input.json | uv run main.py -duration 30 -supply 40
      ```

## Next steps

* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
