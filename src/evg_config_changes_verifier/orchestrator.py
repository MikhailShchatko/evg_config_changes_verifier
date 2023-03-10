"""Orchestrator for evergreen config changes verifier."""
import tempfile
from pathlib import Path
from typing import Set

import inject as inject
import structlog
import yaml

from evg_config_changes_verifier.clients.evg_cli_proxy import EvgCliProxy
from evg_config_changes_verifier.clients.git_cli_proxy import GitCliProxy
from evg_config_changes_verifier.models.evg_models import EvgConfigStates, EvgPatch

LOGGER = structlog.get_logger(__name__)


class VerificationOrchestrator:
    """Orchestrator for evergreen config changes verifier."""

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
        :param target_branch: The branch that patch will be merged onto.
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
                self.git_cli_proxy.apply(patch_file=patch_file_path)

        patched_yaml = yaml.safe_load(self.evg_cli_proxy.evaluate(evg_project_yaml))
        LOGGER.info("Evaluated original and patched evergreen project configuration files.")

        return EvgConfigStates(original_yaml=original_yaml, patched_yaml=patched_yaml)

    @staticmethod
    def check_updated_funcs(evg_config_states: EvgConfigStates) -> Set[str]:
        """
        Check function definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :return: Updated function names.
        """
        updated_funcs = set()
        funcs = evg_config_states.patched_yaml.get("functions", {})
        original_funcs = evg_config_states.original_yaml.get("functions", {})

        for func_name, func_body in funcs.items():
            if func_name not in original_funcs:
                updated_funcs.add(func_name)
                continue

            original_func_body = original_funcs[func_name]
            if str(func_body) != str(original_func_body):
                updated_funcs.add(func_name)

        LOGGER.info("Found updated functions.", funcs=updated_funcs)
        return updated_funcs

    @staticmethod
    def check_updated_tasks(
        evg_config_states: EvgConfigStates, updated_funcs: Set[str]
    ) -> Set[str]:
        """
        Check task definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param updated_funcs: Updated function names.
        :return: Updated task names.
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
            if any(func in updated_funcs for func in task_funcs):
                updated_tasks.add(task_name)

        LOGGER.info("Found updated tasks.", tasks=updated_tasks)
        return updated_tasks

    @staticmethod
    def check_updated_task_groups(
        evg_config_states: EvgConfigStates, updated_funcs: Set[str], updated_tasks: Set[str]
    ) -> Set[str]:
        """
        Check task groups definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param updated_funcs: Updated function names.
        :param updated_tasks: Updated task names.
        :return: Updated task group names.
        """
        updated_task_groups = set()
        original_task_groups_dict = {
            task_group["name"]: task_group
            for task_group in evg_config_states.original_yaml.get("task_groups", [])
        }

        for task_group in evg_config_states.patched_yaml.get("task_groups", []):
            task_group_name = task_group["name"]

            if task_group_name not in original_task_groups_dict:
                updated_tasks.add(task_group_name)
                continue

            original_task_group = original_task_groups_dict[task_group_name]
            if str(task_group) != str(original_task_group):
                updated_tasks.add(task_group_name)
                continue

            if any(task in updated_tasks for task in task_group.get("tasks", [])):
                updated_task_groups.add(task_group_name)
                continue

            task_group_funcs = set()
            for key in ("setup_group", "teardown_group", "setup_task", "teardown_task"):
                if key in task_group and task_group[key] is not None:
                    task_group_funcs.update(
                        command["func"] for command in task_group[key] if "func" in command
                    )
            if any(func in updated_funcs for func in task_group_funcs):
                updated_tasks.add(task_group_name)

        LOGGER.info("Found updated task groups.", task_groups=updated_task_groups)
        return updated_task_groups

    @staticmethod
    def check_updated_build_variants(
        evg_config_states: EvgConfigStates, updated_tasks: Set[str], updated_task_groups: Set[str]
    ) -> EvgPatch:
        """
        Check build variant definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param updated_tasks: Updated task names.
        :param updated_task_groups: Updated task group names.
        :return: Updated build variant and task names.
        """
        updated_variants = set()
        updated_tasks_and_groups = updated_tasks.union(updated_task_groups)
        original_variants_dict = {
            variant["name"]: variant
            for variant in evg_config_states.original_yaml.get("buildvariants", [])
        }

        for variant in evg_config_states.patched_yaml.get("buildvariants", []):
            variant_name = variant["name"]
            variant_tasks = {task["name"] for task in variant.get("tasks", [])}

            if variant_name not in original_variants_dict:
                updated_variants.add(variant_name)
                updated_tasks_and_groups.update(variant_tasks)
                continue

            original_variant = original_variants_dict[variant_name]
            if str(variant.get("expansions", {})) != str(original_variant.get("expansions", {})):
                updated_variants.add(variant_name)
                updated_tasks_and_groups.update(variant_tasks)
                continue

            if str(variant.get("run_on", [])) != str(original_variant.get("run_on", [])):
                updated_variants.add(variant_name)
                updated_tasks_and_groups.update(variant_tasks)
                continue

            original_variant_tasks_dict = {
                task["name"]: task for task in original_variant.get("tasks", [])
            }
            for task in variant.get("tasks", []):
                task_name = task["name"]

                if task_name not in original_variant_tasks_dict:
                    updated_tasks_and_groups.add(task_name)
                    continue

                original_task = original_variant_tasks_dict[task_name]
                if str(task) != str(original_task):
                    updated_tasks_and_groups.add(task_name)

            if any(task in updated_tasks_and_groups for task in variant_tasks):
                updated_variants.add(variant_name)

        return EvgPatch(variants=updated_variants, tasks=updated_tasks_and_groups)
