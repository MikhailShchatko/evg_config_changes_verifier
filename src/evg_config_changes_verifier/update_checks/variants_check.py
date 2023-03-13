"""Check variants definitions updates in evergreen project configuration."""
import structlog

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges, EvgConfigStates
from evg_config_changes_verifier.update_checks.base_check import UpdatesCheck

LOGGER = structlog.get_logger(__name__)


class VariantsCheck(UpdatesCheck):
    """Check variants definitions updates in evergreen project configuration."""

    def check(
        self, evg_config_states: EvgConfigStates, evg_config_changes: EvgConfigChanges
    ) -> None:
        """
        Check build variant definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param evg_config_changes: Evergreen project configuration changes.
        """
        updated_variants = set()
        updated_tasks_and_groups = set()
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

            if any(task in evg_config_changes.tasks_and_groups for task in variant_tasks):
                updated_variants.add(variant_name)

        LOGGER.info(
            "Found updated variants.",
            variants=updated_variants if len(updated_variants) > 0 else None,
            tasks_and_groups=updated_tasks_and_groups
            if len(updated_tasks_and_groups) > 0
            else None,
        )
        evg_config_changes.variants.update(updated_variants)
        evg_config_changes.tasks_and_groups.update(updated_tasks_and_groups)
