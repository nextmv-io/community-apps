# Nextmv Workflows

This directory contains functionality for managing community apps.

## Requirements

- For Python scripts please install the packages in `requirements.txt`:

  ```bash
  pip install -r requirements.txt
  ```

## Use

- To update one or more apps. Standing in the `./nextmv` directory, run:

  ```bash
  python update_apps.py \
    -a app1=version1,app2=version2 \
    -b BUCKET \
    -f FOLDER \
    -m MANIFEST_FILE
  ```
