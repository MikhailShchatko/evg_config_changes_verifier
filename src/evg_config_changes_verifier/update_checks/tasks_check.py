"""Check task definitions updates in evergreen project configuration."""
import structlog

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges, EvgConfigStates
from evg_config_changes_verifier.update_checks.base_check import UpdatesCheck

LOGGER = structlog.get_logger(__name__)


class TasksCheck(UpdatesCheck):
    """Check task definitions updates in evergreen project configuration."""

    def check(
        self, evg_config_states: EvgConfigStates, evg_config_changes: EvgConfigChanges
    ) -> None:
        """
        Check task definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param evg_config_changes: Evergreen project configuration changes.
        """
        updated_tasks = set()
        original_tasks_dict = {
            task["name"]: task for task in evg_config_states.original_yaml.get("tasks", [])
        }

        for task in evg_config_states.patched_yaml.get("tasks", []):
            task_name = task["name"]

            if task_name not in original_tasks_dict:
                updated_tasks.add(task_name)
                continue

            original_task = original_tasks_dict[task_name]
            if str(task) != str(original_task):
                updated_tasks.add(task_name)
                continue

            task_funcs = {
                command["func"] for command in task.get("commands", []) if "func" in command
            }
            if any(func in evg_config_changes.functions for func in task_funcs):
                updated_tasks.add(task_name)

        LOGGER.info("Found updated tasks.", tasks=updated_tasks if len(updated_tasks) > 0 else None)
        evg_config_changes.tasks_and_groups.update(updated_tasks)
