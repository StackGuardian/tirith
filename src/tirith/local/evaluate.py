"""
Discover policy files, mask the input document, and evaluate one policy at a time.

Moved from the GitHub Action, where this was `tirith_action/local.py`, so that both front ends drive
one implementation. See the package docstring for why evaluation shells out.
"""

import glob as _glob
import json
import os
import subprocess
import sys

from ..platform import discover, redact, report


class LocalError(Exception):
    """Local evaluation could not be completed. Always fails closed."""


# Preferred policy naming. A directory holding any of these is treated as an explicit policy
# directory and nothing else in it is considered.
POLICY_SUFFIX = ".tirith.json"

# Per policy. A policy is pure computation over a parsed document, so this only trips on a
# pathological evaluator, but a job that hangs forever is worse than one that fails.
EVALUATION_TIMEOUT = 300

# `meta.enforcement` values that downgrade a failing policy to a warning. Anything unrecognised
# fails instead -- an unlabelled or mislabelled policy must gate, not slip through.
#
# The approval spellings warn rather than gate, matching platform mode, where a policy carrying
# `onFail: APPROVAL_REQUIRED` also warns: the run finishes before the intent is known, so there is
# nothing to approve. Local mode has no approval mechanism at all, so failing closed on it would
# block a change with no way to unblock it.
WARN_ENFORCEMENTS = (
    "soft_mandatory",
    "advisory",
    "warn",
    "warning",
    "low",
    "approval_required",
    "approval-required",
    "approval",
)

# Recognised, and gate. Listed rather than left to the `else` so a correctly-labelled blocking
# policy does not raise the "unrecognised enforcement" warning on every run it fails --
# `hard_mandatory` is what tirith's own golden test pins, so that fired constantly.
FAIL_ENFORCEMENTS = ("hard_mandatory", "mandatory", "fail", "error", "high", "critical", "blocking")


def _looks_like_policy(path):
    """
    Whether a .json file is a tirith policy.

    Load-bearing rather than defensive. A policy directory routinely also holds the document under
    evaluation (`plan.json`), and `--policy-path` accepts a glob that a user may well point at a
    directory full of mixed JSON. Without this check the input document is evaluated *as a policy*,
    which reports a spurious failure and buries the real findings.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False
    return isinstance(data, dict) and "meta" in data and "evaluators" in data


def discover_policies(policy_path):
    """
    Resolve `--policy-path` to a list of policy files.

    A file is taken as given -- if a user names one explicitly, evaluating it is the instruction,
    and reporting "that is not a policy" is more useful than silently skipping it.
    """
    if not policy_path:
        return []

    if os.path.isfile(policy_path):
        return [policy_path]

    if "*" in policy_path or "?" in policy_path:
        matches = sorted(p for p in _glob.glob(policy_path, recursive=True) if os.path.isfile(p))
        return [p for p in matches if _looks_like_policy(p)]

    if os.path.isdir(policy_path):
        explicit = sorted(_glob.glob(os.path.join(policy_path, "**", "*" + POLICY_SUFFIX), recursive=True))
        if explicit:
            return explicit
        candidates = sorted(_glob.glob(os.path.join(policy_path, "**", "*.json"), recursive=True))
        return [p for p in candidates if _looks_like_policy(p)]

    return []


def read_json(path, label):
    """
    Read a JSON document, or raise LocalError.

    Deliberately near-identical to platform.check.read_json rather than shared with it: the two
    raise different exception types, and ten lines is not worth an abstraction that would have to
    take the exception class as a parameter.
    """
    if not os.path.exists(path):
        raise LocalError(f"{label} not found: {path}")
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise LocalError(f"{label} is not valid JSON ({path}): {e}")
    except OSError as e:
        raise LocalError(f"Could not read {label} ({path}): {e}")


def prepare_input(input_path, plan_file, terraform_bin, input_kind, source_dir, scratch, state_path=None):
    """
    Resolve the document to evaluate and mask it, returning (path, redaction_count).

    Masking matters here even though nothing is uploaded. Evaluator messages embed the actual
    attribute values they compared, and those messages are copied verbatim into whatever comment or
    note the caller posts -- so an unmasked local run publishes plan values to a code host. Masking
    also keeps a local verdict identical to the platform one for the same plan, because the platform
    path evaluates the masked document too.

    `json` and `kubernetes` documents are passed through untouched: they carry no sensitivity
    markers to mask by, and tirith reads YAML for them, which a JSON round-trip here would break.
    """
    if input_kind not in ("terraform_plan", "terraform_state"):
        if not input_path:
            raise LocalError(f"--input-path is required when --input-kind is '{input_kind}'.")
        if not os.path.exists(input_path):
            raise LocalError(f"input document not found: {input_path}")
        return input_path, 0

    if input_path and plan_file:
        raise LocalError("--input-path and --plan-file cannot be combined; pass one of them.")

    # `--state-path` is how the platform path is told which document to evaluate for a
    # terraform_state check. Ignoring it here sent local mode to discovery, which finds plan.json --
    # so the two modes evaluated *different documents* from identical inputs, and a violation
    # present only in the state was reported as a pass.
    if input_kind == "terraform_state" and not input_path and not plan_file and state_path:
        input_path = state_path

    if plan_file:
        try:
            document = discover.terraform_show_json(plan_file, binary=terraform_bin or None)
        except discover.DiscoveryError as e:
            raise LocalError(str(e))
    elif input_path:
        document = read_json(input_path, "input document")
    else:
        try:
            resolved = discover.discover_input(source_dir or ".")
        except discover.DiscoveryError as e:
            raise LocalError(str(e))
        document = read_json(resolved, "input document")

    if input_kind == "terraform_state":
        masked = redact.redact_state(document)
    else:
        masked = redact.redact_plan(document)
    redactions = redact.count_redactions(masked)

    masked_path = os.path.join(scratch, "tirith-input.json")
    try:
        with open(masked_path, "w") as f:
            json.dump(masked, f)
    except OSError as e:
        raise LocalError(f"Could not write the masked document to {masked_path}: {e}")

    return masked_path, redactions


def engine_argv(policy_path, input_path):
    """
    The argv used to evaluate one policy.

    `sys.executable -m tirith` rather than a `tirith` on PATH, so the interpreter that evaluates is
    the one whose renderer was imported above -- a `tirith` on PATH could be a different
    installation entirely. Factored out so a test can pin it: see the package docstring for why this
    must stay a subprocess against the frozen `--json` contract.
    """
    return [sys.executable, "-m", "tirith", "-policy-path", policy_path, "-input-path", input_path]


def _evaluate_one(policy_path, input_path):
    """
    Run one policy. Returns (document, error_message); exactly one is set.

    `--json` disables logging process-wide and prints a bare `{}` on failure, so the failure reason
    is not on either stream. When that happens the policy is re-run without `--json` purely to
    recover a message worth showing -- one extra subprocess, only ever on the error path.
    """
    argv = engine_argv(policy_path, input_path)

    try:
        completed = subprocess.run(argv + ["--json"], capture_output=True, text=True, timeout=EVALUATION_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, f"evaluation timed out after {EVALUATION_TIMEOUT}s"
    except OSError as e:
        return None, f"could not run tirith: {e}"

    if completed.returncode != 0:
        return None, _recover_error(argv)

    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "tirith produced no parseable result document"

    if not isinstance(document, dict) or not document:
        return None, _recover_error(argv)

    # A bare {"errors": [...]} with no final_result is what unresolved policy variables produce.
    if "final_result" not in document:
        return None, "; ".join(str(e) for e in document.get("errors") or []) or "no result was produced"

    errors = document.get("errors") or []
    if errors:
        return None, "; ".join(str(e) for e in errors)

    return document, None


def _recover_error(argv):
    """Re-run without --json to get a human-readable reason out of the logger."""
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=EVALUATION_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return "evaluation failed"

    stderr = (completed.stderr or "").strip()
    if stderr:
        # The logger writes a traceback for provider errors; the last line carries the cause.
        return stderr.splitlines()[-1][:500]
    return "evaluation failed"


def _fails(document):
    """
    The failed evaluators, reshaped for the renderer.

    `description` is deliberately dropped rather than passed through. The renderer treats any entry
    carrying a `description` key as a Checkov finding and reads only that field, skipping the
    per-resource messages and addresses entirely -- and tirith's evaluator entries always carry the
    key, often with a null value, which renders as a detail block with nothing in it at all. Sending
    just `result` routes them down the branch written for this shape, which is where the actual
    findings and the resource addresses come from.

    The evaluator description is not lost information worth keeping here: the rule name already
    names the policy in both the table and the summary line, and the messages are specific to the
    resources that failed.
    """
    fails = []
    for evaluator in document.get("evaluators") or []:
        if evaluator.get("passed"):
            continue
        entry = {"result": evaluator.get("result") or []}
        if evaluator.get("id"):
            entry["id"] = evaluator["id"]
        fails.append(entry)
    return fails


def _identity(document, policy_path):
    """(policy_id, rule_name) for a result, falling back to the filename."""
    meta = document.get("meta") or {}
    stem = os.path.basename(policy_path)
    for suffix in (POLICY_SUFFIX, ".json"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    policy_id = meta.get("id") or stem
    return str(policy_id), str(meta.get("name") or policy_id)


def _failure_result(document, on_unknown_enforcement):
    """FAIL, unless the policy labelled itself as advisory."""
    enforcement = (document.get("meta") or {}).get("enforcement")
    if enforcement is None:
        return report.FAIL
    normalised = str(enforcement).strip().lower()
    if normalised in WARN_ENFORCEMENTS:
        return report.WARN
    if normalised in FAIL_ENFORCEMENTS:
        return report.FAIL
    on_unknown_enforcement(str(enforcement))
    return report.FAIL


def evaluate(policy_paths, input_path, on_unknown_enforcement=lambda _: None):
    """
    Evaluate every policy and build the PolicyEvalResults document the renderer consumes.

    Returns (policy_results, errored) where `errored` lists (policy, reason) pairs. A policy that
    could not be evaluated becomes a FAIL rule carrying an `exec_err`, which the renderer surfaces
    as `engine: <reason>`: visible in the report, distinguishable from a real violation, and never
    mistakable for a pass. The caller still fails regardless of --fail-on-error -- "could not
    evaluate" is a tool failure, not a policy decision.
    """
    policy_results = {}
    errored = []

    for policy_path in policy_paths:
        document, error = _evaluate_one(policy_path, input_path)

        if error is not None:
            policy_id, rule_name = _identity({}, policy_path)
            rule = {
                "rule_name": rule_name,
                "result": report.FAIL,
                "evaluations": {"fails": [{"exec_err": f"{policy_path}: {error}"}]},
            }
            errored.append((policy_path, error))
        else:
            policy_id, rule_name = _identity(document, policy_path)
            final = document.get("final_result")
            if final is None:
                rule = {"rule_name": rule_name, "skip": True}
            elif final:
                rule = {"rule_name": rule_name, "result": report.PASS}
            else:
                rule = {
                    "rule_name": rule_name,
                    "result": _failure_result(document, on_unknown_enforcement),
                    "evaluations": {"fails": _fails(document)},
                }

        policy_results.setdefault(policy_id, []).append(rule)

    return policy_results, errored
