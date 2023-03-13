"""Check function definitions updates in evergreen project configuration."""
import structlog

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges, EvgConfigStates
from evg_config_changes_verifier.update_checks.base_check import UpdatesCheck

LOGGER = structlog.get_logger(__name__)


class FunctionsCheck(UpdatesCheck):
    """Check function definitions updates in evergreen project configuration."""

    def check(
        self, evg_config_states: EvgConfigStates, evg_config_changes: EvgConfigChanges
    ) -> None:
        """
        Check function definitions updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param evg_config_changes: Evergreen project configuration changes.
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

        LOGGER.info(
            "Found updated functions.", funcs=updated_funcs if len(updated_funcs) > 0 else None
        )
        evg_config_changes.functions.update(updated_funcs)
