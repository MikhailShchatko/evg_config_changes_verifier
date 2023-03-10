"""Models for working with Evergreen."""
from typing import NamedTuple, Dict, Any, Set


class EvgConfigStates(NamedTuple):
    """
    Evergreen project configuration states.

    * original_yaml: Original state.
    * patched_yaml: Patched state.
    """

    original_yaml: Dict[str, Any]
    patched_yaml: Dict[str, Any]


class EvgPatch(NamedTuple):
    """
    Evergreen patch.

    * variants: Set of build variant names.
    * tasks: Set of task names.
    """

    variants: Set[str]
    tasks: Set[str]

    def as_evg_patch_cmd_args(self) -> str:
        """Make evergreen patch command arguments string."""
        variant_args_str = " ".join(f"-v {v}" for v in self.variants)
        task_args_str = " ".join(f"-t {t}" for t in self.tasks)
        return f"{variant_args_str} {task_args_str}"
