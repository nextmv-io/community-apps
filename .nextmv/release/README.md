# Release

Release one or more apps. Releasing an app means the following.

- The latest version will be available to be cloned via `nextmv community clone`.
- If the app has a marketplace counterpart, the latest version will be pushed.

`cd` into the `release` dir.

- Install the packages.

    ```bash
    pip install -r requirements.txt
    ```

- Execute the release for the desired apps.

    ```bash
    python main.py \
      -apps app1,app2 \
      -bucket BUCKET \
      -folder FOLDER \
      -manifest MANIFEST_FILE
    ```
