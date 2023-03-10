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
    help="The branch that the current changes will be merged onto.",
)
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging.")
def main(evg_project_config: Path, target_branch: str, verbose: bool) -> None:
    """Evergreen project configuration changes verifier."""
    configure_logging(verbose)
    LOGGER.info("Comparing original and patched evergreen project configuration files.")

    def dependencies(binder: inject.Binder) -> None:
        binder.bind_to_constructor(EvgCliProxy, EvgCliProxy.create)
        binder.bind_to_constructor(GitCliProxy, GitCliProxy.create)

    inject.configure(dependencies)
    orchestrator = inject.instance(VerificationOrchestrator)

    evg_config_states = orchestrator.get_evg_config_states(evg_project_config, target_branch)
    updated_funcs = orchestrator.check_updated_funcs(evg_config_states)
    updated_tasks = orchestrator.check_updated_tasks(evg_config_states, updated_funcs)
    updated_task_groups = orchestrator.check_updated_task_groups(
        evg_config_states, updated_funcs, updated_tasks
    )
    evg_patch = orchestrator.check_updated_build_variants(
        evg_config_states, updated_tasks, updated_task_groups
    )

    print(evg_patch.as_evg_patch_cmd_args())


if __name__ == "__main__":
    main()
