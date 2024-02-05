"""
This script updates one or more applications by:

1. Updating the version.
2. Updating the SDK version (if the app is written in Go).
3. Updating the manifest file and uploading it.

Execute from the ./nextmv directory:

```bash
python update_apps.py \
    -a app1=version1,app2=version2 \
    -b BUCKET \
    -f FOLDER \
    -m MANIFEST_FILE
```
"""

import argparse
import copy
import os
import subprocess
from typing import Any

import yaml
from boto3 import client as s3Client

parser = argparse.ArgumentParser(description="Update community apps in the Marketplace.")
parser.add_argument(
    "--apps",
    "-a",
    type=str,
    help="Apps to release, with the version. Example: knapsack-gosdk=v1.0.0,knapsack-pyomo=v1.0.0",
    required=True,
)
parser.add_argument(
    "--bucket",
    "-b",
    type=str,
    help="S3 bucket.",
    required=True,
)
parser.add_argument(
    "--folder",
    "-f",
    type=str,
    help="S3 bucket folder.",
    required=True,
)
parser.add_argument(
    "--manifest",
    "-m",
    type=str,
    help="Manifest file.",
    required=True,
)
args = parser.parse_args()


def main():
    """
    Entry point for the script.
    """

    apps = [
        {
            "name": app.split("=")[0],
            "version": app.split("=")[1],
        }
        for app in args.apps.split(",")
    ]
    apps.sort(key=lambda x: x["name"])
    client = s3Client("s3")

    manifest = get_manifest(
        client=client,
        bucket=args.bucket,
        folder=args.folder,
        manifest_file=args.manifest,
    )
    workflow_configuration = read_yaml(
        filepath=os.path.join(os.getcwd(), "workflow-configuration.yml"),
    )
    for app in apps:
        if "v" not in app["version"]:
            app["version"] = f"v{app['version']}"

        update_app(
            name=app["name"],
            version=app["version"],
            workflow_configuration=workflow_configuration,
        )
        manifest = update_manifest(manifest, app)

    upload_manifest(
        client=client,
        bucket=args.bucket,
        folder=args.folder,
        manifest_file=args.manifest,
        manifest=manifest,
    )


def get_manifest(
    client: s3Client,
    bucket: str,
    folder: str,
    manifest_file: str,
) -> dict[str, Any]:
    """Returns the manifest from the S3 bucket."""

    result = client.get_object(Bucket=bucket, Key=f"{folder}/{manifest_file}")
    return yaml.safe_load(result["Body"].read())


def read_yaml(filepath: str) -> dict[str, Any]:
    """Returns the YAML file in the path."""

    with open(filepath) as f:
        return yaml.safe_load(f)


def update_app(name: str, version: str, workflow_configuration: dict[str, Any]):
    """Updates the app with the new version."""

    workflow_info = {}
    for app in workflow_configuration["apps"]:
        if app["name"] == name:
            workflow_info = app
            break

    with open(os.path.join(os.getcwd(), "..", name, "VERSION"), "w") as f:
        f.write(version + "\n")

    if workflow_info["type"] == "go":
        sdk_version = workflow_info["sdk_version"]
        if "v" not in sdk_version:
            sdk_version = f"v{sdk_version}"

        _ = subprocess.run(
            ["go", "get", f"github.com/nextmv-io/sdk@{sdk_version}"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.join("..", name),
        )
        _ = subprocess.run(
            ["go", "mod", "tidy"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.join("..", name),
        )


def update_manifest(
    old: dict[str, Any],
    app: dict[str, Any],
) -> dict[str, Any]:
    """Updates the manifest with the new apps."""

    new = copy.deepcopy(old)
    for manifest_app in new["apps"]:
        if manifest_app["name"] == app["name"]:
            manifest_app["latest"] = app["version"]
            manifest_app["versions"].append(app["version"])
            break

    return new


def upload_manifest(
    client: s3Client,
    bucket: str,
    folder: str,
    manifest_file: str,
    manifest: dict[str, Any],
):
    """Uploads the manifest to the S3 bucket."""

    class Dumper(yaml.Dumper):
        """Custom YAML dumper that does not use the default flow style."""

        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    client.put_object(
        Bucket=bucket,
        Key=f"{folder}/{manifest_file}",
        Body=yaml.dump(manifest, Dumper=Dumper, default_flow_style=False),
    )


if __name__ == "__main__":
    main()
