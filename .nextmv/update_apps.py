"""
This script updates one or more applications by:

1. Updating the version.
2. Updating the SDK version (if the app is written in Go).
3. Creating a tarball of the app.
4. Uploading the tarball to the S3 bucket.
5. Pushing the app to Nextmv Marketplace.
6. Updating and uploading the manifest file.

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
import sys
import tarfile
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
    bucket = args.bucket
    folder = args.folder
    manifest_file = args.manifest

    manifest = get_manifest(
        client=client,
        bucket=bucket,
        folder=folder,
        manifest_file=manifest_file,
    )
    for app in apps:
        name = app["name"]
        version = app["version"]
        if "v" not in version:
            version = f"v{version}"

        update_app(name=name, version=version)
        tarball = tar_app(name=name, version=version)
        upload_tarball(
            client=client,
            bucket=bucket,
            folder=folder,
            name=name,
            version=version,
            tarball=tarball,
        )
        push_app(name=name, version=version)
        manifest = update_manifest(manifest, app)

    upload_manifest(
        client=client,
        bucket=args.bucket,
        folder=args.folder,
        manifest_file=args.manifest,
        manifest=manifest,
    )


def app_workflow_info(name: str) -> dict[str, Any]:
    """Gets the app information from the workflow configuration."""

    log(f"Getting workflow info for app: {name}")

    workflow_configuration = read_yaml(
        filepath=os.path.join(os.getcwd(), "workflow-configuration.yml"),
    )
    workflow_info = {}
    for app in workflow_configuration["apps"]:
        if app["name"] == name:
            workflow_info = app
            break

    log(f"Obtained workflow info for app {name}: {workflow_info}")

    return workflow_info


def get_manifest(
    client: s3Client,
    bucket: str,
    folder: str,
    manifest_file: str,
) -> dict[str, Any]:
    """Returns the manifest from the S3 bucket."""

    log("Getting manifest from S3 bucket.")

    result = client.get_object(Bucket=bucket, Key=f"{folder}/{manifest_file}")
    manifest = yaml.safe_load(result["Body"].read())

    log("Obtained manifest from S3 bucket.")

    return manifest


def log(message: str):
    """Logs a message to the console."""

    print(message, file=sys.stdout, flush=True)


def push_app(name: str, version: str):
    """Pushes the app to the Nextmv Marketplace."""

    log(f"Pushing app: {name}; version: {version} to the Marketplace.")

    workflow_info = app_workflow_info(name)
    app_id = workflow_info.get("app_id") or None
    marketplace_app_id = workflow_info.get("marketplace_app_id", "") or None
    if app_id is None or marketplace_app_id is None:
        return

    try:
        result = subprocess.run(
            ["bash", "push_app.sh"],
            env=os.environ
            | {
                "APP_DIR": os.path.join("..", name),
                "APP_ID": app_id,
                "MARKETPLACE_APP_ID": marketplace_app_id,
                "VERSION_ID": version,
            },
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        raise Exception(e.stderr) from e

    log(f"Pushed app: {name}; version: {version} to the Marketplace.")


def read_yaml(filepath: str) -> dict[str, Any]:
    """Returns the YAML file in the path."""

    with open(filepath) as f:
        return yaml.safe_load(f)


def tar_app(name: str, version: str) -> str:
    """Create a tarbal of the app. Returns the name of the tarball."""

    log(f"Creating tarball for app: {name}; version: {version}")

    app_dir = os.path.join(os.getcwd(), "..", name)
    filename = f"{name}_{version}.tar.gz"

    with tarfile.open(filename, "w:gz") as tar:
        tar.add(app_dir, arcname=os.path.basename(app_dir))

    log(f"Created tarball for app: {name}; version: {version}")

    return filename


def update_app(name: str, version: str):
    """Updates the app with the new version."""

    log(f"Updating app: {name}; version: {version}")

    workflow_info = app_workflow_info(name)

    with open(os.path.join(os.getcwd(), "..", name, "VERSION"), "w") as f:
        f.write(version + "\n")

    if workflow_info["type"] == "go":
        sdk_version = workflow_info["sdk_version"]
        if sdk_version != "latest" and "v" not in sdk_version:
            sdk_version = f"v{sdk_version}"

        log(f"Updating SDK for app: {name}; version: {version}; SDK version: {sdk_version}")

        try:
            result = subprocess.run(
                ["go", "get", f"github.com/nextmv-io/sdk@{sdk_version}"],
                check=True,
                capture_output=True,
                text=True,
                cwd=os.path.join("..", name),
            )
            print(result.stdout)

        except subprocess.CalledProcessError as e:
            raise Exception(e.stderr) from e

        try:
            result = subprocess.run(
                ["go", "mod", "tidy"],
                check=True,
                capture_output=True,
                text=True,
                cwd=os.path.join("..", name),
            )
            print(result.stdout)

        except subprocess.CalledProcessError as e:
            raise Exception(e.stderr) from e

    log(f"Updated app: {name}; version: {version}")


def update_manifest(
    old: dict[str, Any],
    app: dict[str, Any],
) -> dict[str, Any]:
    """Updates the manifest with the new apps."""

    log(f"Updating manifest with app: {app}.")

    name = app["name"]
    version = app["version"]

    new = copy.deepcopy(old)
    manifest_apps = new["apps"]

    for manifest_app in manifest_apps:
        if name == manifest_app["name"]:
            versions = manifest_app["versions"]
            manifest_app["latest"] = version
            if version not in versions:
                versions.append(version)
            break

    log(f"Updated manifest with app: {app}.")

    return new


def upload_manifest(
    client: s3Client,
    bucket: str,
    folder: str,
    manifest_file: str,
    manifest: dict[str, Any],
):
    """Uploads the manifest to the S3 bucket."""

    log("Uploading manifest to S3 bucket.")

    class Dumper(yaml.Dumper):
        """Custom YAML dumper that does not use the default flow style."""

        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    client.put_object(
        Bucket=bucket,
        Key=f"{folder}/{manifest_file}",
        Body=yaml.dump(manifest, Dumper=Dumper, default_flow_style=False),
    )

    log("Uploaded manifest to S3 bucket.")


def upload_tarball(
    client: s3Client,
    bucket: str,
    folder: str,
    name: str,
    version: str,
    tarball: str,
):
    """Uploads the tarball to the S3 bucket."""

    log(f"Uploading tarball to S3 bucket: {name}; version: {version}; tarball: {tarball}.")

    with open(tarball, "rb") as f:
        client.put_object(
            Bucket=bucket,
            Key=f"{folder}/{name}/{version}/{tarball}",
            Body=f,
        )

    os.remove(tarball)

    log(f"Uploaded tarball to S3 bucket: {name}; version: {version}; removed tarball: {tarball}.")


if __name__ == "__main__":
    main()
