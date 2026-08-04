"""
Find the document to evaluate without being told where it is.

Exists so a caller with a plan in the conventional place needs no configuration at all. It lives
here rather than in the GitHub Action so GitLab, Jenkins and a local shell get the same behaviour.

`terraform show -json` is also run from here, so a caller never has to write an unmasked plan to
disk at all -- see `terraform_show_json` for why resolving the right binary matters.
"""

import json
import os
import shutil
import subprocess

# Tried in order. Two names, not a glob: a glob over *.json would sweep up an infracost breakdown or
# a package manifest and evaluate it as a plan.
PLAN_FILENAMES = ("plan.json", "tfplan.json")


class DiscoveryError(Exception):
    """No document could be resolved. Always fails closed."""


def discover_input(source_dir):
    """
    Find the plan document in `source_dir`, by convention.

    Two matches is an error rather than "first one wins". Silently evaluating the wrong document
    would report a verdict about infrastructure the caller did not ask about, and look like a pass.
    """
    directory = source_dir or "."
    found = [name for name in PLAN_FILENAMES if os.path.isfile(os.path.join(directory, name))]

    if not found:
        raise DiscoveryError(
            f"No plan document found in {os.path.abspath(directory)}. Expected one of "
            f"{' or '.join(PLAN_FILENAMES)}. Either write one with "
            f"`terraform show -json tfplan > plan.json`, point --plan-file at the binary plan, or "
            f"pass --input-path explicitly."
        )

    if len(found) > 1:
        raise DiscoveryError(
            f"Found {' and '.join(found)} in {os.path.abspath(directory)} and cannot tell which to "
            f"evaluate. Pass --input-path to choose."
        )

    return os.path.join(directory, found[0])


def _resolve_binary(explicit=None):
    """
    Find a terraform/tofu binary, preferring the real one over a wrapper.

    `hashicorp/setup-terraform` installs a JS wrapper as `terraform` and moves the real binary to
    `terraform-bin`. That wrapper calls `core.setOutput('stdout', ...)`, so invoking it for
    `show -json` appends the *entire plan* to $GITHUB_OUTPUT -- an unmasked plan written to a file
    every later step in the job can read. `opentofu/setup-opentofu` does the same with `tofu-bin`.

    So the `-bin` names come first, and the wrappers are only a last resort.
    """
    if explicit:
        return explicit

    candidates = []
    for env_var, binary in (("TERRAFORM_CLI_PATH", "terraform-bin"), ("TOFU_CLI_PATH", "tofu-bin")):
        directory = os.environ.get(env_var)
        if directory:
            candidates.append(os.path.join(directory, binary))
    candidates += ["terraform-bin", "tofu-bin", "terraform", "tofu"]

    for candidate in candidates:
        if os.path.isabs(candidate):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        else:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

    raise DiscoveryError(
        "No terraform or tofu binary found on PATH. Pass --terraform-bin, or write the plan JSON "
        "yourself and pass --input-path."
    )


def terraform_show_json(plan_file, workdir=None, binary=None):
    """
    Render a binary plan to JSON in memory.

    The point is that nothing unmasked touches the disk: the JSON is parsed straight off the pipe
    and handed to the masker. stdout is never logged, for the same reason.
    """
    executable = _resolve_binary(binary)
    if not binary and os.environ.get("TERRAFORM_CLI_PATH") and os.path.basename(executable) == "terraform":
        # Only reachable if the -bin names were all absent, which means the wrapper was installed
        # without its usual layout. Say so rather than silently leaking the plan into $GITHUB_OUTPUT.
        raise DiscoveryError(
            "TERRAFORM_CLI_PATH is set but no terraform-bin was found beside it, so the only "
            "terraform on PATH is the setup-terraform wrapper. Running it would copy the whole plan "
            "into $GITHUB_OUTPUT. Pass --terraform-bin with the real binary."
        )

    directory = workdir or os.path.dirname(os.path.abspath(plan_file)) or "."
    plan_arg = os.path.abspath(plan_file)

    try:
        completed = subprocess.run(
            [executable, "show", "-json", plan_arg],
            cwd=directory,
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise DiscoveryError(f"Could not run `{executable} show -json`: {e}")

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace").strip()[:2000]
        raise DiscoveryError(f"`{executable} show -json` failed (exit {completed.returncode}): {stderr}")

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as e:
        # Deliberately does not echo stdout: on the wrapper path it would be the whole plan.
        raise DiscoveryError(f"`{executable} show -json` did not produce JSON: {e}")
