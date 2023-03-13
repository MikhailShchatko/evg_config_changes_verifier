import logging
import sys
from pathlib import Path

import click
import inject as inject
import structlog
from structlog.stdlib import LoggerFactory

from evg_config_changes_verifier.clients.evg_cli_proxy import EvgCliProxy
from evg_config_changes_verifier.clients.git_cli_proxy import GitCliProxy
from evg_config_changes_verifier.orchestrator import VerificationOrchestrator

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LOGGERS = [
    "inject",
]
DEFAULT_EVG_PROJECT_CONFIG = "etc/evergreen.yml"
DEFAULT_TARGET_BRANCH = "origin/master"


def configure_logging(verbose: bool) -> None:
    """
    Configure logging.

    :param verbose: Enable verbose logging.
    """
    structlog.configure(logger_factory=LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(levelname)s] %(message)s",
        level=level,
        stream=sys.stderr,
    )
    for log_name in EXTERNAL_LOGGERS:
        logging.getLogger(log_name).setLevel(logging.WARNING)


@click.command(context_settings=dict(max_content_width=100, show_default=True))
@click.option(
    "--evg-project-config",
    type=click.Path(exists=True),
    default=DEFAULT_EVG_PROJECT_CONFIG,
    help="Evergreen project configuration file.",
)
@click.option(
    "--target-branch",
    type=str,
    default=DEFAULT_TARGET_BRANCH,
    help="The branch that the current changes will be merged into.",
)
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging.")
def main(evg_project_config: Path, target_branch: str, verbose: bool) -> None:
    """
    Evergreen project configuration changes verifier.

    This tool analyses evergreen project configuration changes and evaluates what build variants and
    tasks are affected by the changes. As a result it will print out the command line arguments for
    `evergreen patch` command with build variant and task names. Those arguments can be passed to
    the `evergreen patch` command to create an evergreen patch to test the changes.

    Currently, the tool supports detecting changes only within evaluated evergreen yaml project
    configuration file.

    Example

    Suppose you've made some evergreen yaml project configuration changes.

        \b
        git diff

        \b
        diff --git a/etc/evergreen_yml_components/definitions.yml b/etc/evergreen_yml_components/definitions.yml
        index 10b165f676e..bf571c827bb 100644
        --- a/etc/evergreen_yml_components/definitions.yml
        +++ b/etc/evergreen_yml_components/definitions.yml
        @@ -3536,6 +3536,7 @@ tasks:
           - command: manifest.load
           - func: "git get project and add git tag"
           - *f_expansions_write
        +  - *f_expansions_write
           - *kill_processes
           - *cleanup_environment
           - func: "set up venv"

    Let's run `verify-evg-config-changes` command.

        \b
        verify-evg-config-changes

        \b
        [2023-03-13 18:32:51,368 - evg_config_changes_verifier.cli - INFO] 2023-03-13 18:32:51 [info     ] Comparing original and patched evergreen project configuration files.
        [2023-03-13 18:33:03,872 - evg_config_changes_verifier.services.evg_config_service - INFO] 2023-03-13 18:33:03 [info     ] Evaluated original and patched evergreen project configuration files.
        [2023-03-13 18:33:03,875 - evg_config_changes_verifier.update_checks.functions_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated functions.       funcs=None
        [2023-03-13 18:33:03,882 - evg_config_changes_verifier.update_checks.tasks_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated tasks.           tasks={'lint_yaml'}
        [2023-03-13 18:33:03,884 - evg_config_changes_verifier.update_checks.task_groups_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated task groups.     task_groups=None
        [2023-03-13 18:33:03,913 - evg_config_changes_verifier.update_checks.variants_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated variants.        tasks_and_groups=None variants={'linux-x86-dynamic-compile-required', 'commit-queue'}
        ---------------------------------------------------------------
        Arguments to create evergreen patch with to verify the changes:
        -v linux-x86-dynamic-compile-required -v commit-queue -t lint_yaml

    Now those arguments can be used to create an evergreen patch.
    """
    configure_logging(verbose)
    LOGGER.info("Comparing original and patched evergreen project configuration files.")

    def dependencies(binder: inject.Binder) -> None:
        binder.bind_to_constructor(EvgCliProxy, EvgCliProxy.create)
        binder.bind_to_constructor(GitCliProxy, GitCliProxy.create)

    inject.configure(dependencies)
    orchestrator = inject.instance(VerificationOrchestrator)

    evg_config_changes = orchestrator.get_evg_config_changes(evg_project_config, target_branch)
    print("---------------------------------------------------------------")
    print("Arguments to create evergreen patch with to verify the changes:")
    print(evg_config_changes.as_evg_patch_cmd_args())


if __name__ == "__main__":
    main()
