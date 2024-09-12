import os
import subprocess
import tarfile
from datetime import datetime

import nextmv
from boto3 import client as s3Client
from log import log
from manifest import Manifest
from workflow_configuration import WorkflowApp, WorkflowConfiguration


def main():
    """
    Entry point for the script.
    """

    options = nextmv.Options(
        nextmv.Parameter("apps", str, description="Apps to release, comma-separated.", required=True),
        nextmv.Parameter("bucket", str, description="S3 bucket.", required=True),
        nextmv.Parameter("folder", str, description="S3 bucket folder.", required=True),
        nextmv.Parameter("manifest", str, description="Manifest file.", required=True),
    )

    apps = [
        {
            "name": app,
        }
        for app in options.apps.split(",")
    ]
    apps.sort(key=lambda x: x["name"])
    client = s3Client("s3")
    bucket = options.bucket
    folder = options.folder
    manifest_file = options.manifest

    workflow_configuration = WorkflowConfiguration.from_yaml(
        filepath=os.path.join(os.getcwd(), "..", "workflow-configuration.yml"),
    )
    manifest = Manifest.from_s3(
        client=client,
        bucket=bucket,
        folder=folder,
        manifest_file=manifest_file,
        workflow_configuration=workflow_configuration,
    )

    for app in apps:
        name = app["name"]
        workflow_app = workflow_configuration.get_app(name)

        log(f"Releasing app: {name}.")

        app_version = manifest.app_version(name)
        new_app_version = bump_app_version(app_version)
        log(f"App: {name}; current version: {app_version}; new version: {new_app_version}.")

        marketplace_version = manifest.marketplace_version(name)
        new_marketplace_version = bump_marketplace_version(marketplace_version, workflow_app)
        log(
            f"App: {name}; current marketplace version: {marketplace_version}; "
            f"new marketplace version: {new_marketplace_version}."
        )

        tarball = tar_app(name=name, version=new_app_version)
        upload_tarball(
            client=client,
            bucket=bucket,
            folder=folder,
            name=name,
            version=new_app_version,
            tarball=tarball,
        )
        push_app(
            name=name,
            version=new_marketplace_version,
            workflow_app=workflow_app,
        )

        manifest.update(
            app_name=name,
            app_version=new_app_version,
            marketplace_version=new_marketplace_version,
            workflow_app=workflow_app,
        )

    manifest.upload(
        client=client,
        bucket=options.bucket,
        folder=options.folder,
        manifest_file=options.manifest,
    )


def push_app(name: str, version: str, workflow_app: WorkflowApp):
    """
    Pushes the app to the Nextmv Marketplace.
    """

    log(f"Pushing app: {name}; version: {version} to the Marketplace.")

    if not workflow_app.is_marketplace():
        log(f"App: {name} either app_id or marketplace_app_id is not defined; skipping push to Cloud.")
        return

    app_id = workflow_app.app_id
    marketplace_app_id = workflow_app.marketplace_app_id

    try:
        result = subprocess.run(
            ["bash", "push_app.sh"],
            env=os.environ
            | {
                "APP_DIR": os.path.join("../..", name),
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
        raise Exception(
            f"error attempting app push: {name}; version: {version}; "
            f"app_id: {app_id}; marketplace_app_id: {marketplace_app_id}: {e.stderr}"
        ) from e

    log(f"Pushed app: {name}; version: {version} to the Marketplace.")


def tar_app(name: str, version: str) -> str:
    """
    Create a tarbal of the app. Returns the name of the tarball.
    """

    log(f"Creating tarball for app: {name}; version: {version}.")

    app_dir = os.path.join(os.getcwd(), "../..", name)
    filename = f"{name}_{version}.tar.gz"

    with tarfile.open(filename, "w:gz") as tar:
        tar.add(app_dir, arcname=os.path.basename(app_dir))

    log(f"Created tarball for app: {name}; version: {version}.")

    return filename


def upload_tarball(
    client: s3Client,
    bucket: str,
    folder: str,
    name: str,
    version: str,
    tarball: str,
):
    """
    Uploads the tarball to the S3 bucket.
    """

    log(f"Uploading tarball to S3 bucket: {name}; version: {version}; tarball: {tarball}.")

    with open(tarball, "rb") as f:
        client.put_object(
            Bucket=bucket,
            Key=f"{folder}/{name}/{version}/{tarball}",
            Body=f,
        )

    os.remove(tarball)

    log(f"Uploaded tarball to S3 bucket: {name}; version: {version}; removed tarball: {tarball}.")


def bump_app_version(version: str | None = None) -> str:
    """
    Bumps the version based on the current one. The app version is based on
    today’s date and a counter that is incremented if there is more than one
    release a day.
    """

    today = datetime.today().strftime("%Y%m%d")
    basic_version = f"v{today}.0"

    if version is None or version == "":
        return basic_version

    parts = version.split(".")
    if len(parts) == 1:
        return basic_version

    if parts[0].strip("v") == today:
        count = int(parts[1])
        return f"v{today}.{count + 1}"

    return basic_version


def bump_marketplace_version(
    version: str | None = None,
    workflow_app: WorkflowApp | None = None,
) -> str | None:
    """
    Bumps the marketplace version based on the current one. The marketplace
    version roughly follows semantic versioning. The minor version is the one
    that is automatically bumped. We use a v to precede the version number.
    """

    if not workflow_app.is_marketplace():
        return None

    basic_version = "v0.1.0"
    if version is None or version == "":
        return basic_version

    parts = version.split(".")
    if len(parts) == 1:
        return basic_version

    major = int(parts[0][1:])
    workflow_major = int(workflow_app.marketplace_major_version[1:])
    minor = int(parts[1])
    patch = int(parts[2])

    if major < workflow_major:
        major = workflow_major
        minor = 0
        patch = 0
    elif major == workflow_major:
        minor += 1
        patch = 0
    else:
        raise Exception(
            f"App {workflow_app.name} has a higher major version {major} "
            f"than the current marketplace major version {workflow_major}."
        )

    return f"v{major}.{minor}.{patch}"


if __name__ == "__main__":
    main()
