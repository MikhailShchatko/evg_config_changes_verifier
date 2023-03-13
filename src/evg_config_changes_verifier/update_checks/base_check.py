"""An interface to check evergreen project configuration updates."""
import abc

from evg_config_changes_verifier.models.evg_models import EvgConfigChanges, EvgConfigStates


class UpdatesCheck(abc.ABC):
    """An interface to check evergreen project configuration updates."""

    @abc.abstractmethod
    def check(
        self, evg_config_states: EvgConfigStates, evg_config_changes: EvgConfigChanges
    ) -> None:
        """
        Check evergreen project configuration updates.

        :param evg_config_states: Original and patched Evergreen project configuration states.
        :param evg_config_changes: Evergreen project configuration changes.
        """
        raise NotImplementedError()
