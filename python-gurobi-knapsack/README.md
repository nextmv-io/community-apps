# Nextmv Python Gurobi Knapsack

Example for running a Python application on the Nextmv Platform using the
Gurobi solver. We solve a knapsack Mixed Integer Programming problem.

If you have a Gurobi WSL license, remove the `.template` extension from the
`gurobi.lic.template` file and replace the contents with your actual license
key. Modify the `app.yaml` file to include the `gurobi.lic` in the files list.

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json -duration 30
    ```

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
