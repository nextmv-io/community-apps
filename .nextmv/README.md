# Nextmv Workflows

This directory contains functionality for managing community apps.

## Update Apps

### Update Apps Requirements

- For Python scripts please install the packages in `requirements.txt`:

  ```bash
  pip install -r requirements.txt
  ```

### Update Apps Usage

- To update one or more apps. Standing in the `./nextmv` directory, run:

  ```bash
  python update_apps.py \
    -a app1=version1,app2=version2 \
    -b BUCKET \
    -f FOLDER \
    -m MANIFEST_FILE
  ```

## Run README Tests

### README Tests Requirements

Make sure the local environment is set according to the associated
[readme-test workflow](../.github/workflows/readme-test.yml). This encompasses the
main language versions denoted by [workflow-configuration.yml](workflow-configuration.yml)
as well. Any additional requirements given by `requirements.txt` files will be
installed automatically by the script.

### README Tests Usage

To run the tests, standing in the `./nextmv` directory, run:

```bash
python run_readme_tests.py
```
