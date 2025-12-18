# Nextmv Python Simpy Carwash Simulation

Example for running a Python application on the Nextmv Platform using the Simpy
library. We simulate a carwash with limited washing machines and random car
arrivals.

<!-- markdownlint-disable MD013 -->

1. Install packages.

    ```bash
    pip3 install -r requirements.txt
    ```

1. Run the app.

    ```bash
    python3 main.py -input input.json -output output.json -random_seed -1 -sim_time 20
    ```

1. Create local runs of the app.

    ```bash
    python3 app.py -action local -input_file input.json
    ```

1. Export your Nextmv API key as an environment variable.

    ```bash
    export NEXTMV_API_KEY="<YOUR_API_KEY>"
    ```

1. Sync the local app with the cloud.

    ```bash
    python3 app.py -action sync -app_id carwash-sim -app_name "Carwash Simulation"
    ```

<!-- markdownlint-enable MD013 -->

## Next steps

* Open `main.py` and modify the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
