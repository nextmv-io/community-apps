"""
This script updates the manifest file with the latest version of the release
and the apps. It assumes that there is a `manifest.yml` file which corresponds
to the old manifest. It writes the new manifest to `new_manifest.yml`. Versions
are taken from the `VERSION` file in each app directory, and the root.

Execute from the root:

```bash
python scripts/update_manifest.py
```
"""
import copy
import os
from typing import Any

import yaml


def main():
    """
    Entry point for the script.
    """

    apps = [
        {
            "name": app["name"],
            "type": app["type"],
            "version": version(dir=app["name"]),
        }
        for app in open_yaml_file(filepath="workflow-configuration.yml")["apps"]
    ]
    apps.sort(key=lambda x: x["name"])
    old = open_yaml_file(filepath="manifest.yml")
    new = update_manifest(old=old, apps=apps)
    with open("new_manifest.yml", "w") as f:
        yaml.dump(new, f)


def update_manifest(
    old: dict[str, Any],
    apps: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Updates the manifest with the new apps.

    Args:
        old: The old manifest.
        apps: The list of apps.

    Returns:
        The new manifest.
    """

    new = copy.deepcopy(old)
    new_version = version(dir=".")
    new["latest"] = new_version
    release = {
        "version": new_version,
        "apps": apps,
    }
    new["releases"].append(release)

    return new


def open_yaml_file(filepath: str) -> dict[str, Any]:
    """
    Returns the YAML file in the path.

    Args:
        filepath: The path of the file.

    Returns:
        The content of the YAML file.

    Raises:
        FileNotFoundError: If the file is not found.
    """

    with open(filepath) as f:
        return yaml.safe_load(f)


def version(dir: str) -> str:
    """
    Returns the version in the given directory.

    Args:
        dir: The directory.

    Returns:
        The version.

    Raises:
        FileNotFoundError: If the VERSION file is not found.
    """

    with open(os.path.join(dir, "VERSION")) as f:
        return f.read().strip()


if __name__ == "__main__":
    main()
