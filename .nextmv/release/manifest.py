from dataclasses import dataclass

import yaml
from boto3 import client as s3Client
from log import log
from workflow_configuration import AppType, WorkflowApp, WorkflowConfiguration

NAME_TRANSLATIONS = {
    "knapsack-gosdk": "go-highs-knapsack",
    "knapsack-java-ortools": "java-ortools-knapsack",
    "knapsack-ortools": "python-ortools-knapsack",
    "knapsack-pyomo": "python-pyomo-knapsack",
    "nextroute": "go-nextroute",
    "order-fulfillment-gosdk": "go-highs-orderfulfillment",
    "routing-ortools": "python-ortools-routing",
    "shift-assignment-ortools": "python-ortools-shiftassignment",
    "shift-assignment-pyomo": "python-pyomo-shiftassignment",
    "shift-planning-ortools": "python-ortools-shiftplanning",
    "shift-planning-pyomo": "python-pyomo-shiftplanning",
    "shift-scheduling-gosdk": "go-highs-shiftscheduling",
    "xpress": "python-xpress-knapsack",
    "cost-flow-ortools": "python-ortools-costflow",
    "knapsack-ampl": "python-ampl-knapsack",
    "knapsack-gurobi": "python-gurobi-knapsack",
    "routing-java-ortools": "java-ortools-routing",
    "demand-forecasting-ortools": "python-ortools-demandforecasting",
    "knapsack-ortools-csv": "python-ortools-knapsack-multicsv",
    "facility-location-ampl": "python-ampl-facilitylocation",
    "price-optimization-ampl": "python-ampl-priceoptimization",
    "knapsack-highs": "python-highs-knapsack",
    "routing-pyvroom": "python-pyvroom-routing",
    "hello-world": "python-hello-world",
    "knapsack-pyoptinterface": "python-pyoptinterface-knapsack",
}


@dataclass
class App:
    """Represents an app in the manifest."""

    description: str | None = None
    latest_app_version: str | None = None
    latest_marketplace_version: str | None = None
    name: str | None = None
    type: AppType | None = None
    app_versions: list[str] | None = None
    marketplace_versions: list[str] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, any],
        workflow_configuration: WorkflowConfiguration,
    ) -> "App":
        """Creates an app from a dictionary."""

        original_name = data.get("name", None)
        name = NAME_TRANSLATIONS.get(original_name, original_name)

        workflow_app = workflow_configuration.get_app(name)
        if workflow_app is None:
            raise ValueError(f"App: {name} not found in the workflow configuration.")

        latest_marketplace_version = data.get("latest_marketplace_version", None)
        marketplace_versions = data.get("marketplace_versions", [])
        latest_app_version = data.get("latest_app_version", None)
        app_versions = data.get("app_versions", [])

        old_schema = (
            "versions" in data
            and "latest" in data
            and "latest_app_version" not in data
            and "latest_marketplace_version" not in data
            and "app_versions" not in data
            and "marketplace_versions" not in data
        )
        if old_schema:
            latest_marketplace_version = data.get("latest", None)
            marketplace_versions = data.get("versions", None)

        if not workflow_app.is_marketplace():
            latest_marketplace_version = None
            marketplace_versions = []

        return cls(
            description=workflow_app.description,
            latest_app_version=latest_app_version,
            latest_marketplace_version=latest_marketplace_version,
            name=name,
            type=workflow_app.type,
            app_versions=app_versions,
            marketplace_versions=marketplace_versions,
        )

    def update_app_version(self, version: str):
        """Updates the app version."""

        if self.app_versions is None:
            self.app_versions = []

        if version not in self.app_versions:
            self.app_versions.append(version)

        self.latest_app_version = version

    def update_marketplace_version(self, version: str):
        """Updates the marketplace version."""

        if self.marketplace_versions is None:
            self.marketplace_versions = []

        if version not in self.marketplace_versions:
            self.marketplace_versions.append(version)

        self.latest_marketplace_version = version

    def to_dict(self) -> dict[str, any]:
        """Returns the app as a dictionary."""

        return {
            "description": self.description,
            "latest_app_version": self.latest_app_version,
            "latest_marketplace_version": self.latest_marketplace_version,
            "name": self.name,
            "type": self.type.value,
            "app_versions": self.app_versions,
            "marketplace_versions": self.marketplace_versions,
        }


@dataclass
class Manifest:
    """Represents the manifest file."""

    apps: list[App] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, any],
        workflow_configuration: WorkflowConfiguration,
    ) -> "Manifest":
        """Creates a manifest from a dictionary."""

        apps = []
        if data != {}:
            apps = [App.from_dict(app, workflow_configuration) for app in data["apps"]]

        # Check that every app in the workflow configuration is in the
        # manifest.
        for app in workflow_configuration.apps:
            if app.name not in [a.name for a in apps]:
                log(f"App: {app.name} not found in the manifest, adding from workflow configuration.")
                apps.append(
                    App(
                        description=app.description,
                        latest_app_version=None,
                        latest_marketplace_version=None,
                        name=app.name,
                        type=app.type,
                    )
                )

        return cls(apps=apps)

    @classmethod
    def from_s3(
        cls,
        client: s3Client,
        bucket: str,
        folder: str,
        manifest_file: str,
        workflow_configuration: WorkflowConfiguration,
    ) -> "Manifest":
        """Instantiates the manifest from the S3 bucket."""

        log("Getting manifest from S3 bucket.")

        manifest = {}
        try:
            result = client.get_object(Bucket=bucket, Key=f"{folder}/{manifest_file}")
            manifest = yaml.safe_load(result["Body"].read())
            log("Obtained manifest from S3 bucket.")

        except client.exceptions.NoSuchKey:
            log("No manifest in S3 bucket.")
            pass

        return Manifest.from_dict(manifest, workflow_configuration)

    def app_version(self, name: str) -> str:
        """Returns the latest app version for the given app name."""

        for app in self.apps:
            if app.name == name:
                return app.latest_app_version

        return None

    def marketplace_version(self, name: str) -> str:
        """Returns the latest marketplace version for the given app name."""

        for app in self.apps:
            if app.name == name:
                return app.latest_marketplace_version

        return None

    def to_dict(self) -> dict[str, any]:
        """Returns the manifest as a dictionary."""

        return {
            "apps": [app.to_dict() for app in self.apps],
        }

    def update(
        self,
        app_name: str,
        app_version: str,
        marketplace_version: str,
        workflow_app: WorkflowApp,
    ):
        """Updates the manifest with the given information."""

        log(
            f"Updating manifest with app: {app_name}; "
            f"app_version: {app_version}; marketplace_version: {marketplace_version}."
        )

        found = False
        for app in self.apps:
            if app_name != app.name:
                continue

            app.update_app_version(app_version)

            if workflow_app.is_marketplace():
                app.update_marketplace_version(marketplace_version)

            app.description = workflow_app.description

            found = True
            break

        if not found:
            self.apps.append(
                App(
                    description=workflow_app.description,
                    latest_app_version=app_version,
                    latest_marketplace_version=marketplace_version,
                    name=app_name,
                    type=workflow_app.type,
                    app_versions=[app_version],
                    marketplace_versions=[marketplace_version],
                )
            )

        # Always sort the apps by name.
        self.apps = sorted(self.apps, key=lambda x: x.name)

        log(f"Updated manifest with app: {app_name}.")

    def upload(
        self,
        client: s3Client,
        bucket: str,
        folder: str,
        manifest_file: str,
    ):
        """Uploads the manifest to the S3 bucket."""

        log("Uploading manifest to S3 bucket.")

        class Dumper(yaml.Dumper):
            """Custom YAML dumper that does not use the default flow style."""

            def increase_indent(self, flow=False, indentless=False):
                return super().increase_indent(flow, False)

        manifest = self.to_dict()
        body = yaml.dump(manifest, Dumper=Dumper, default_flow_style=False)
        client.put_object(
            Bucket=bucket,
            Key=f"{folder}/{manifest_file}",
            Body=body,
        )

        log("Uploaded manifest to S3 bucket.")
