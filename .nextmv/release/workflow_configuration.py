from dataclasses import dataclass
from enum import Enum

import yaml
from log import log


class AppType(str, Enum):
    """Represents the type of app."""

    GO = "go"
    PYTHON = "python"
    JAVA = "java"


@dataclass
class WorkflowApp:
    """Represents an app in the workflow configuration."""

    name: str | None = None
    type: AppType | None = None
    app_id: str | None = None
    marketplace_app_id: str | None = None
    marketplace_major_version: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "WorkflowApp":
        """Creates an app from a dictionary."""

        return cls(
            name=data["name"],
            type=AppType(data["type"]),
            app_id=data.get("app_id"),
            marketplace_app_id=data.get("marketplace_app_id"),
            marketplace_major_version=data.get("marketplace_major_version"),
            description=data.get("description"),
        )

    def is_marketplace(self) -> bool:
        """Returns whether the app is a marketplace app."""

        return (
            self.marketplace_app_id is not None
            and self.app_id is not None
            and self.marketplace_major_version is not None
        )


@dataclass
class WorkflowConfiguration:
    """Represents the workflow configuration."""

    apps: list[WorkflowApp] | None = None

    @classmethod
    def from_yaml(cls, filepath: str) -> "WorkflowConfiguration":
        """Creates a workflow configuration from a YAML file."""

        with open(filepath) as file:
            data = yaml.safe_load(file)

        apps = [WorkflowApp.from_dict(app) for app in data["apps"]]

        log(f"Loaded {len(apps)} apps from {filepath} in workflow configuration.")

        return cls(apps=apps)

    def get_app(self, name: str) -> WorkflowApp | None:
        """Returns the app with the given name."""

        for app in self.apps:
            if app.name == name:
                return app

        return None
