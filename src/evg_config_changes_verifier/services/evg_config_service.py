"""Service for working with evergreen project configurations."""
import tempfile
from pathlib import Path

import inject
import structlog
import yaml

from evg_config_changes_verifier.clients.evg_cli_proxy import EvgCliProxy
from evg_config_changes_verifier.clients.git_cli_proxy import GitCliProxy
from evg_config_changes_verifier.models.evg_models import EvgConfigStates

LOGGER = structlog.get_logger(__name__)


class EvgConfigService:
    """Service for working with evergreen project configurations."""

    @inject.autoparams()
    def __init__(self, git_cli_proxy: GitCliProxy, evg_cli_proxy: EvgCliProxy) -> None:
        """
        Initialize.

        :param git_cli_proxy: Proxy for interacting with Git CLI.
        :param evg_cli_proxy: Proxy for interacting with Evergreen CLI.
        """
        self.git_cli_proxy = git_cli_proxy
        self.evg_cli_proxy = evg_cli_proxy

    def get_evg_config_states(self, evg_project_yaml: Path, target_branch: str) -> EvgConfigStates:
        """
        Get evaluated original and patched Evergreen project configuration states.

        :param evg_project_yaml: Location of Evergreen project configuration.
        :param target_branch: The branch that patch will be merged into.
        :return: Original and patched Evergreen project configuration states.
        """
        with tempfile.NamedTemporaryFile() as tf:
            patch_file_path = Path(tf.name)
            self.git_cli_proxy.diff(
                no_pager=True, target_branch=target_branch, output_file=patch_file_path
            )
            self.git_cli_proxy.apply(patch_file=patch_file_path, reverse=True)
            try:
                original_yaml = yaml.safe_load(self.evg_cli_proxy.evaluate(evg_project_yaml))
            finally:
                # Make sure that we don't mess up local git repo state
                self.git_cli_proxy.apply(patch_file=patch_file_path)

        patched_yaml = yaml.safe_load(self.evg_cli_proxy.evaluate(evg_project_yaml))
        LOGGER.info("Evaluated original and patched evergreen project configuration files.")

        return EvgConfigStates(original_yaml=original_yaml, patched_yaml=patched_yaml)
