# Nextmv Python OR-Tools Cost Flow

Example for running a Python application on the Nextmv Platform using the
OR-Tools package. We solve a minimum cost flow problem for assigning workers to
projects.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json \
      -duration 30 -penalty 3000
    ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
