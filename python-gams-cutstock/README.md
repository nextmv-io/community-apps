# Nextmv GAMS Cutstock Problem

Example for running a Python application on the Nextmv Platform using the GAMS
[control API](https://www.gams.com/latest/docs/API_PY_CONTROL.html). We solve a
cutting stock problem that finds the minimum number of cuts required to satisfy
the product demand.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input data.json -output output.json \
      -raw_width 100 -max_pattern 35
    ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
