# Nextmv GAMSPy Traveling Salesman Problem

Example for running a Python application on the Nextmv Platform using [GAMSPy](https://gamspy.readthedocs.io/en/latest/) to model the problem. We solve the traveling salesman problem that minimizes the total distance travelled while visiting each city exactly once.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input data.json -output output.json \
      -maxnodes 5
    ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact