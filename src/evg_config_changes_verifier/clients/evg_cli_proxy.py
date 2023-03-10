"""Proxy for working with Evergreen CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from plumbum import local
from plumbum.machines.local import LocalCommand

LOGGER = structlog.get_logger(__name__)


class EvgCliProxy:
    """A proxy for interacting with Evergreen CLI."""

    def __init__(self, evg_cli: LocalCommand) -> None:
        """
        Initialize.

        :param evg_cli: Object for executing cli command.
        """
        self.evg_cli = evg_cli

    @classmethod
    def create(cls) -> EvgCliProxy:
        """
        Create Evergreen CLI service instance.

        :return: Evergreen CLI service instance
        """
        return cls(local.cmd.evergreen)

    def evaluate(
        self, project_config_location: Path, output_file: Optional[Path] = None
    ) -> Optional[str]:
        """
        Evaluate the given evergreen project configuration.

        :param project_config_location: Location of project configuration to evaluate.
        :param output_file: Write output to file.
        :return: Evaluated project configuration.
        """
        args = ["evaluate", "--path", project_config_location]
        if output_file is not None:
            args.append([">", output_file])
        return self.evg_cli[args]()
