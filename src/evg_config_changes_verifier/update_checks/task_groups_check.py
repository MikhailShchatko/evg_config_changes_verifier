"""Check task group definitions updates in evergreen project configuration."""
import structlog

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges, EvgConfigStates
from evg_config_changes_verifier.update_checks.base_check import UpdatesCheck

LOGGER = structlog.get_logger(__name__)


class TaskGroupsCheck(UpdatesCheck):
    """Check task group definitions updates in evergreen project configuration."""

    def check(
        self, evg_config_states: EvgConfigStates, evg_config_changes: EvgConfigChanges
    ) -> None:
        """
        Check task groups definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param evg_config_changes: Evergreen project configuration changes.
        """
        updated_task_groups = set()
        original_task_groups_dict = {
            task_group["name"]: task_group
            for task_group in evg_config_states.original_yaml.get("task_groups", [])
        }

        for task_group in evg_config_states.patched_yaml.get("task_groups", []):
            task_group_name = task_group["name"]

            if task_group_name not in original_task_groups_dict:
                updated_task_groups.add(task_group_name)
                continue

            original_task_group = original_task_groups_dict[task_group_name]
            if str(task_group) != str(original_task_group):
                updated_task_groups.add(task_group_name)
                continue

            if any(
                task in evg_config_changes.tasks_and_groups for task in task_group.get("tasks", [])
            ):
                updated_task_groups.add(task_group_name)
                continue

            task_group_funcs = set()
            for key in ("setup_group", "teardown_group", "setup_task", "teardown_task"):
                if key in task_group and task_group[key] is not None:
                    task_group_funcs.update(
                        command["func"] for command in task_group[key] if "func" in command
                    )
            if any(func in evg_config_changes.functions for func in task_group_funcs):
                updated_task_groups.add(task_group_name)

        LOGGER.info(
            "Found updated task groups.",
            task_groups=updated_task_groups if len(updated_task_groups) > 0 else None,
        )
        evg_config_changes.tasks_and_groups.update(updated_task_groups)
