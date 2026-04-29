# Nextmv Python Hexaly Knapsack

Example for running a Python application on the Nextmv Platform using the
Hexaly solver while reading data from multiple Excel (.xlsx) files. We solve a
multi knapsack Mixed Integer Programming problem.

1. Setup license:
    1. **Local**: If you have a Hexaly license, remove the `.template`
       extension from the `license.dat.template` file and replace the contents
       with your actual license key. Modify the `app.yaml` file to include the
       `license.dat` in the files list.
    1. **Platform**: Don't forget to also define the license file as a
        [secret][secret] in your Nextmv Application as well. This can be easily
        done via [console][console].
        - Define a file secret with the name `license.dat` and the content of
          your license file.
        - Define an environment variable secret with the name `LD_LIBRARY_PATH`
          and the value `./lib` to point Hexaly to the bundled `*.so` libraries.

1. Install packages.

   - With `pip`

      ```bash
      pip install .
      ```

   - With `uv`
  
      ```bash
      uv sync
      ```

1. Put your model file and any other necessary files in the `inputs/` directory.
   The _model file_ should have the extension `.hxm`. All other files need to be
   either referenced by your model code or specified as input arguments via
   options (e.g., `-data=<file>`). See the example files in the `inputs/`
   directory for reference.
   - The model automatically loads the first `.hxm` file (alternatively, the
     first `.lsp` file) it finds in the input directory.

1. Run the app.

   - With `python`

      ```bash
      python main.py inFileName=inputs/input.dat solFileName=output.txt
      ```

   - With `uv`

      ```bash
      uv run main.py inFileName=inputs/input.dat solFileName=output.txt
      ```

1. If above steps were successful, you can push the app to the Nextmv Platform.
   E.g., using the [Nextmv CLI][install-cli]:

    ```bash
    nextmv cloud app push --app-id <your-app-id>
    ```

1. You can then run the app on the Nextmv Platform by using the CLI (note that
   you need to have the license file defined as a [secret][secret] in your
   Nextmv Application):

    ```bash
    nextmv cloud run create --app-id <your-app-id> \
        --input inputs/ \
        --secret-collection-id <your-secret-collection> \
        --options 'inFileName=input.dat,solFileName=output.txt'
    ```

   Or you can run it via the [Nextmv Console][console].

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

<!-- markdownlint-disable MD013 -->
```bash
docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/python:3.11 \
sh -c 'pip install /app && python3 /app/main.py'
```
<!-- markdownlint-enable MD013 -->

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by
using the command `Dev Containers: Reopen in Container`.

## Next steps

- Open `main.py` and modify the model.
- Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[console]: https://cloud.nextmv.io
[secret]: https://www.nextmv.io/docs/using-nextmv/reference/secret-collections
[install-cli]: https://docs.nextmv.io/docs/using-nextmv/setup/install#nextmv-cli
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
