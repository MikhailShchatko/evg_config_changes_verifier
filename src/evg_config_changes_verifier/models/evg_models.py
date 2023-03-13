"""Models for working with Evergreen."""
from __future__ import annotations

from typing import Any, Dict, NamedTuple, Set


class EvgConfigStates(NamedTuple):
    """
    Evergreen project configuration states.

    * original_yaml: Original state.
    * patched_yaml: Patched state.
    """

    original_yaml: Dict[str, Any]
    patched_yaml: Dict[str, Any]


class EvgConfigChanges(NamedTuple):
    """
    Evergreen project configuration changes.

    * functions: Set of changed function names.
    * tasks_and_groups: Set of changed task and task group names.
    * variants: Set of changed build variant names.
    """

    functions: Set[str]
    tasks_and_groups: Set[str]
    variants: Set[str]

    @classmethod
    def create_empty(cls) -> EvgConfigChanges:
        """
        Create empty Evergreen project configuration changes instance.

        :return: Empty Evergreen project configuration changes instance.
        """
        return cls(
            functions=set(),
            tasks_and_groups=set(),
            variants=set(),
        )

    def as_evg_patch_cmd_args(self) -> str:
        """Make evergreen patch command arguments string."""
        variant_args_str = " ".join(f"-v {v}" for v in self.variants)
        task_args_str = " ".join(f"-t {t}" for t in self.tasks_and_groups)
        return f"{variant_args_str} {task_args_str}"
