import argparse
import os
import tomllib
from dataclasses import dataclass

import requests

# The packages to check for updates by default.
PACKAGES = [
    "nextmv",
    "nextpipe",
    "nextroute",
    "nextmv-scikit-learn",
    "nextmv-gurobipy",
]


@dataclass
class PackageUpdate:
    project: str
    package: str
    current_version: str
    latest_version: str


def parse_args():
    parser = argparse.ArgumentParser(description="Check for package updates.")
    parser.add_argument(
        "--packages",
        "-p",
        nargs="+",
        default=PACKAGES,
        help="List of packages to check for updates.",
    )
    parser.add_argument(
        "--slack-url",
        "-s",
        type=str,
        default=None,
        help="Slack webhook URL to send notifications.",
    )
    return parser.parse_args()


def get_latest_version(package: str) -> str:
    """Gets the latest version of a package from PyPI."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package}/json")
        latest_version = response.json()["info"]["version"]
        return latest_version
    except Exception as e:
        print(f"Error fetching version for {package}: {e}")
        return ""


def get_dependencies_requirements(path: str, packages: list[str]) -> dict:
    """Reads the dependencies from requirements.txt."""
    dependencies = {}
    try:
        with open(path) as f:
            for line in f:
                if "==" in line:
                    package, version = line.strip().split("==")
                    dependencies[package] = version
    except FileNotFoundError:
        print("requirements.txt not found.")
    return {k: v for k, v in dependencies.items() if k in packages}


def get_dependencies_pyproject(path: str, packages: list[str]) -> dict:
    """Reads the dependencies from pyproject.toml."""
    dependencies = {}
    try:
        with open(path) as f:
            pyproject = tomllib.load(f)
            deps = pyproject.get("dependencies", [])
            for dep in deps:
                if "==" in dep:
                    package, version = dep.split("==")
                    dependencies[package] = version
    except FileNotFoundError:
        print("pyproject.toml not found.")
    return {k: v for k, v in dependencies.items() if k in packages}


def get_projects_dependencies(packages: list[str]) -> dict:
    """Gets the dependency managing files for all projects."""
    project_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
    dependencies = {}
    # Walk all directories in the project directory (skipping hidden ones)
    for root, _, files in os.walk(project_dir):
        if any(part.startswith(".") for part in root.split(os.sep)):
            continue
        project_name = os.path.basename(root)
        # Only consider one dependency file per directory (prefer requirements.txt)
        if "requirements.txt" in files:
            req_path = os.path.join(root, "requirements.txt")
            deps = get_dependencies_requirements(req_path, packages)
            if deps:
                dependencies[project_name] = deps
        elif "pyproject.toml" in files:
            pyproject_path = os.path.join(root, "pyproject.toml")
            deps = get_dependencies_pyproject(pyproject_path, packages)
            if deps:
                dependencies[project_name] = deps
    return dependencies


def check_for_updates(packages: list[str]) -> list[PackageUpdate]:
    """Checks for updates for the specified packages."""
    updates = []
    projects_dependencies = get_projects_dependencies(packages)
    latest_versions = {pkg: get_latest_version(pkg) for pkg in packages}
    for project, deps in projects_dependencies.items():
        for package, current_version in deps.items():
            latest_version = latest_versions.get(package, "")
            if latest_version:
                if current_version != latest_version:
                    updates.append(
                        PackageUpdate(
                            project=project,
                            package=package,
                            current_version=current_version,
                            latest_version=latest_version,
                        )
                    )
    updates.sort(key=lambda x: (x.project, x.package))
    return updates


def get_search_and_replace_recommendations(updates: list[PackageUpdate]) -> dict[str, str]:
    """Generates search and replace recommendations for updating packages."""
    recommendations = {}
    for update in updates:
        search = f"{update.package}=={update.current_version}"
        replace = f"{update.package}=={update.latest_version}"
        recommendations[search] = replace
    return recommendations


def send_slack_notification(webhook_url: str, updates: list[PackageUpdate]):
    """Sends a Slack notification with the updates."""
    comm_apps = "<https://github.com/nextmv-io/community-apps|community-apps>"
    message = f"The following packages in {comm_apps} have updates available:\n"
    for update in updates:
        message += f"- {update.project} / {update.package}: {update.current_version} -> {update.latest_version}\n"

    recos = get_search_and_replace_recommendations(updates)
    message += "Search & replace recommendations:\n"
    for search, replace in recos.items():
        message += f"`{search}` -> `{replace}`\n"

    try:
        response = requests.post(webhook_url, json={"text": message})
        if response.status_code != 200:
            print(f"Failed to send Slack notification: {response.text}")
    except Exception as e:
        print(f"Error sending Slack notification: {e}")


def main():
    args = parse_args()
    updates = check_for_updates(args.packages)
    if updates:
        print("The following packages have updates available:")
        for update in updates:
            print(f"- {update.project}/{update.package}: {update.current_version} -> {update.latest_version}")
        recos = get_search_and_replace_recommendations(updates)
        print("\nSearch & replace recommendations:")
        for search, replace in recos.items():
            print(f"`{search}` -> `{replace}`")
        if args.slack_url:
            send_slack_notification(args.slack_url, updates)
    else:
        print("All packages are up to date.")


if __name__ == "__main__":
    main()
