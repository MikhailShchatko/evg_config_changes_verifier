"""Orchestrator for evergreen config changes verifier."""
from pathlib import Path

import inject as inject
import structlog

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges
from evg_config_changes_verifier.services.evg_config_service import EvgConfigService
from evg_config_changes_verifier.update_checks.functions_check import FunctionsCheck
from evg_config_changes_verifier.update_checks.task_groups_check import TaskGroupsCheck
from evg_config_changes_verifier.update_checks.tasks_check import TasksCheck
from evg_config_changes_verifier.update_checks.variants_check import VariantsCheck

LOGGER = structlog.get_logger(__name__)

UPDATE_CHECKS = (
    # Order matters
    FunctionsCheck(),
    TasksCheck(),
    TaskGroupsCheck(),
    VariantsCheck(),
)


class VerificationOrchestrator:
    """Orchestrator for evergreen config changes verifier."""

    @inject.autoparams()
    def __init__(self, evg_config_service: EvgConfigService) -> None:
        """
        Initialize.

        :param evg_config_service: Service for working with evergreen project configurations.
        """
        self.evg_config_service = evg_config_service

    def get_evg_config_changes(
        self, evg_project_yaml: Path, target_branch: str
    ) -> EvgConfigChanges:
        """
        Get evergreen project configuration changes.

        :param evg_project_yaml: Location of Evergreen project configuration.
        :param target_branch: The branch that patch will be merged into.
        :return: Evergreen project configuration changes.
        """
        evg_config_states = self.evg_config_service.get_evg_config_states(
            evg_project_yaml, target_branch
        )
        evg_config_changes = EvgConfigChanges.create_empty()
        for update in UPDATE_CHECKS:
            update.check(evg_config_states, evg_config_changes)
        return evg_config_changes
