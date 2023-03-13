# Evergreen project configuration changes verifier

This tool analyses evergreen project configuration changes and evaluates what build variants and
tasks are affected by the changes. As a result it will print out the command line arguments for
`evergreen patch` command with build variant and task names. Those arguments can be passed to
the `evergreen patch` command to create an evergreen patch to test the changes.

Currently, the tool supports detecting changes only within evaluated evergreen yaml project
configuration file.

## Dependencies

* Python 3.9 or later
* Git CLI
* Evergreen CLI

## Installation

We strongly recommend using a tool like [pipx](https://pypa.github.io/pipx/) to install
this tool. This will isolate the dependencies and ensure they don't conflict with other tools.

```bash
pipx install git+https://github.com/MikhailShchatko/evg_config_changes_verifier
```

## Usage

```bash
verify-evg-config-changes --help
```

## Example

Suppose you've made some evergreen yaml project configuration changes.

```bash
git diff

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
```

Let's run `verify-evg-config-changes` command.

```bash
verify-evg-config-changes

[2023-03-13 18:32:51,368 - evg_config_changes_verifier.cli - INFO] 2023-03-13 18:32:51 [info     ] Comparing original and patched evergreen project configuration files.
[2023-03-13 18:33:03,872 - evg_config_changes_verifier.services.evg_config_service - INFO] 2023-03-13 18:33:03 [info     ] Evaluated original and patched evergreen project configuration files.
[2023-03-13 18:33:03,875 - evg_config_changes_verifier.update_checks.functions_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated functions.       funcs=None
[2023-03-13 18:33:03,882 - evg_config_changes_verifier.update_checks.tasks_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated tasks.           tasks={'lint_yaml'}
[2023-03-13 18:33:03,884 - evg_config_changes_verifier.update_checks.task_groups_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated task groups.     task_groups=None
[2023-03-13 18:33:03,913 - evg_config_changes_verifier.update_checks.variants_check - INFO] 2023-03-13 18:33:03 [info     ] Found updated variants.        tasks_and_groups=None variants={'linux-x86-dynamic-compile-required', 'commit-queue'}
---------------------------------------------------------------
Arguments to create evergreen patch with to verify the changes:
-v linux-x86-dynamic-compile-required -v commit-queue -t lint_yaml
```

Now those arguments can be used to create an evergreen patch.
