"""Proxy for working with Git CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from plumbum import local
from plumbum.machines.local import LocalCommand

LOGGER = structlog.get_logger(__name__)


class GitCliProxy:
    """A proxy for interacting with Git CLI."""

    def __init__(self, git_cli: LocalCommand) -> None:
        """
        Initialize.

        :param git_cli: Object for executing cli command.
        """
        self.git_cli = git_cli

    @classmethod
    def create(cls) -> GitCliProxy:
        """
        Create Git CLI service instance.

        :return: Git CLI service instance.
        """
        return cls(local.cmd.git)

    def diff(
        self,
        no_pager: Optional[bool],
        target_branch: Optional[str],
        output_file: Optional[Path],
    ) -> Optional[str]:
        """
        Run git-diff command.

        :param no_pager: Do not pipe Git output into a pager.
        :param target_branch: The branch that patch will be merged into.
        :param output_file: Output to a patch file that can be applied with git-apply.
        :return: Git-diff command output.
        """
        args = []
        if no_pager:
            args.append("--no-pager")
        args.append("diff")
        if target_branch is not None:
            args.extend(["--merge-base", target_branch])
        if output_file is not None:
            args.extend(["--output", output_file, "--binary"])
        return self.git_cli[args]()

    def apply(self, patch_file: Path, reverse: Optional[bool] = False) -> None:
        """
        Run git-apply command.

        :param patch_file: The file to read the patch from.
        :param reverse: Apply the patch in reverse.
        """
        args = ["apply", "--allow-empty"]
        if reverse:
            args.append("--reverse")
        args.append(patch_file)
        self.git_cli[args]()
