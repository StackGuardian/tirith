"""
Check a policy document before handing it to the engine.

The engine assumes a well-formed policy: `start_policy_evaluation_from_dict` reads
`policy_dict.get("meta")` and immediately calls `.get()` on it, so a policy with no `meta`
raises AttributeError from inside core rather than reporting a problem. Under the CLI that is
merely a bad error message; in the playground, where the user is *editing* the policy and it is
malformed on almost every keystroke, an exception is the normal case and a traceback is not an
acceptable way to render it.

So this validates first and returns problems as data. It is deliberately separate from the
engine and not imported by it: the engine's behaviour is pinned by golden-file tests, and
making it stricter would change what it accepts for every existing caller.

Findings are advisory. `check_policy` returns errors (the engine will fail or misbehave) and
warnings (it will run, but probably not as intended) so the UI can show both without refusing
to evaluate -- experimenting with a half-written policy is the point of a playground.
"""

import re
from typing import Any, Dict, List, NamedTuple, Tuple

from ..core.evaluators import EVALUATORS_DICT
from ..providers import PROVIDERS_DICT
from . import schema

# Mirrors core.final_evaluator's own substitution: it rewrites && || ! and then compiles what
# is left, so an id must survive as a Python name.
_ID_PATTERN = re.compile(r"^\w+$")


class Finding(NamedTuple):
    severity: str  # "error" | "warning"
    # Where in the document, as a human-readable path like `evaluators[2].condition.type`.
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def _error(where: str, message: str) -> Finding:
    return Finding("error", where, message)


def _warning(where: str, message: str) -> Finding:
    return Finding("warning", where, message)


def check_policy(policy: Any) -> List[Finding]:
    """
    Validate a parsed policy document.

    :param policy: The parsed policy, which may be any JSON value -- the caller may be handing
                   us whatever their editor buffer currently parses to.
    :return:       Findings, worst first. Empty means the engine will accept it.
    """
    if not isinstance(policy, dict):
        return [_error("<root>", f"A policy must be a JSON object, not {type(policy).__name__}.")]

    findings: List[Finding] = []
    provider_name = _check_meta(policy, findings)
    declared_ids = _check_evaluators(policy, provider_name, findings)
    _check_eval_expression(policy, declared_ids, findings)

    # Errors first so a UI showing only the first line shows the blocking one.
    return sorted(findings, key=lambda f: 0 if f.severity == "error" else 1)


def _check_meta(policy: Dict, findings: List[Finding]) -> str:
    meta = policy.get("meta")
    if meta is None:
        # Not merely invalid: core calls policy_meta.get(...) unguarded, so this is the input
        # that raises AttributeError from inside the engine.
        findings.append(_error("meta", "Missing. A policy needs a `meta` object naming its provider."))
        return ""
    if not isinstance(meta, dict):
        findings.append(_error("meta", f"Must be an object, not {type(meta).__name__}."))
        return ""

    if "version" not in meta:
        findings.append(_warning("meta.version", 'Not set. Convention is "v1".'))

    # core defaults this to "core", which is not in PROVIDERS_DICT -- so every check then fails
    # with "Provider 'core' is not found". Naming it explicitly is effectively required.
    provider_name = meta.get("required_provider")
    if not provider_name:
        findings.append(
            _error(
                "meta.required_provider",
                "Not set. Without it the engine looks for a provider named 'core', which does not exist.",
            )
        )
        return ""
    if provider_name not in PROVIDERS_DICT:
        known = ", ".join(sorted(PROVIDERS_DICT))
        findings.append(_error("meta.required_provider", f"Unknown provider '{provider_name}'. Known: {known}."))
        return ""
    return provider_name


def _check_evaluators(policy: Dict, provider_name: str, findings: List[Finding]) -> List[str]:
    evaluators = policy.get("evaluators")
    if evaluators is None:
        findings.append(_error("evaluators", "Missing. A policy needs at least one check."))
        return []
    if not isinstance(evaluators, list):
        findings.append(_error("evaluators", f"Must be a list, not {type(evaluators).__name__}."))
        return []
    if not evaluators:
        findings.append(_warning("evaluators", "Empty, so this policy checks nothing."))
        return []

    declared_ids: List[str] = []
    seen = set()

    for index, evaluator in enumerate(evaluators):
        where = f"evaluators[{index}]"
        if not isinstance(evaluator, dict):
            findings.append(_error(where, f"Must be an object, not {type(evaluator).__name__}."))
            continue

        check_id = evaluator.get("id")
        if not check_id:
            findings.append(_error(f"{where}.id", "Missing. Every check needs an id to be named in eval_expression."))
        elif not isinstance(check_id, str):
            findings.append(_error(f"{where}.id", f"Must be a string, not {type(check_id).__name__}."))
        else:
            declared_ids.append(check_id)
            if check_id in seen:
                # The results dict is keyed by id, so the later check silently replaces the
                # earlier one in the final expression.
                findings.append(_error(f"{where}.id", f"Duplicate id '{check_id}'; ids must be unique."))
            seen.add(check_id)
            if not _ID_PATTERN.match(check_id):
                # Only a warning, and the distinction is subtle enough to be worth stating.
                # core substitutes ids into the expression by regex *before* parsing it, so a
                # defined `eval-id-1` becomes `True` and never reaches the parser as
                # subtraction -- several shipped fixtures rely on this and evaluate correctly.
                # It breaks only if the same id is left undefined, where the surviving `-`
                # raises ValueError out of the engine; _check_eval_expression reports that
                # case as an error separately.
                findings.append(
                    _warning(
                        f"{where}.id",
                        f"'{check_id}' contains characters other than letters, digits and underscores. "
                        f"It works while it is defined, but becomes a hard error if it is ever "
                        f"dropped from eval_expression.",
                    )
                )

        _check_provider_args(evaluator, provider_name, where, findings)
        _check_condition(evaluator, where, findings)

    return declared_ids


def _check_provider_args(evaluator: Dict, provider_name: str, where: str, findings: List[Finding]) -> None:
    provider_args = evaluator.get("provider_args")
    if provider_args is None:
        findings.append(_error(f"{where}.provider_args", "Missing. This says what to read from the input."))
        return
    if not isinstance(provider_args, dict):
        findings.append(_error(f"{where}.provider_args", f"Must be an object, not {type(provider_args).__name__}."))
        return

    described = schema.PROVIDERS.get(provider_name)
    if described is None:
        # Provider is real but the TUI has no description of it, or meta was already invalid.
        # Either way there is nothing further to check here, and the earlier finding covers it.
        return

    if not described.uses_operation_type:
        (only_operation,) = described.operations
        _check_args_against(provider_args, only_operation, f"{where}.provider_args", findings)
        return

    operation_name = provider_args.get("operation_type")
    if not operation_name:
        known = ", ".join(op.name for op in described.operations)
        findings.append(_error(f"{where}.provider_args.operation_type", f"Missing. Expected one of: {known}."))
        return

    operation = schema.operation_for(provider_name, operation_name)
    if operation is None:
        known = ", ".join(op.name for op in described.operations)
        findings.append(
            _error(
                f"{where}.provider_args.operation_type",
                f"'{operation_name}' is not supported by {provider_name}. Expected one of: {known}.",
            )
        )
        return

    _check_args_against(provider_args, operation, f"{where}.provider_args", findings)


def _check_args_against(provider_args: Dict, operation: schema.Operation, where: str, findings: List[Finding]) -> None:
    for arg in operation.args:
        if arg.required and arg.name not in provider_args:
            findings.append(_error(f"{where}.{arg.name}", f"Required by operation '{operation.name}'. {arg.help}"))
        value = provider_args.get(arg.name)
        if arg.choices and value is not None and value not in arg.choices:
            findings.append(_error(f"{where}.{arg.name}", f"'{value}' is not one of: {', '.join(arg.choices)}."))

    known_names = {arg.name for arg in operation.args} | {"operation_type"}
    for key in provider_args:
        if key not in known_names:
            # A warning, not an error: providers ignore arguments they do not read, so this
            # runs -- it just does not do what the extra key suggests. Usually a typo.
            findings.append(
                _warning(f"{where}.{key}", f"Not read by operation '{operation.name}'; it will be ignored.")
            )


def _check_condition(evaluator: Dict, where: str, findings: List[Finding]) -> None:
    condition = evaluator.get("condition")
    if condition is None:
        findings.append(_error(f"{where}.condition", "Missing. This says what the value must satisfy."))
        return
    if not isinstance(condition, dict):
        findings.append(_error(f"{where}.condition", f"Must be an object, not {type(condition).__name__}."))
        return

    evaluator_name = condition.get("type")
    if not evaluator_name:
        findings.append(_error(f"{where}.condition.type", "Missing. Name the evaluator to apply."))
    elif evaluator_name not in EVALUATORS_DICT:
        known = ", ".join(sorted(EVALUATORS_DICT))
        findings.append(_error(f"{where}.condition.type", f"'{evaluator_name}' is not an evaluator. Known: {known}."))
    else:
        info = schema.EVALUATORS.get(evaluator_name)
        # Deliberately no type check on a "list" evaluator's value. ContainedIn and its
        # negation branch explicitly on str (substring), list (membership) and dict (subset),
        # so demanding a list would reject working policies -- the value_kind is a hint about
        # which widget the builder shows, not a constraint the engine imposes.
        pattern = condition.get("value")
        if info and info.value_kind == "regex" and isinstance(pattern, str):
            try:
                re.compile(pattern)
            except re.error as e:
                findings.append(_error(f"{where}.condition.value", f"Not a valid regular expression: {e}."))

    # `value` is genuinely optional for IsEmpty/IsNotEmpty and required otherwise, but a null
    # value is meaningful (the kubernetes fixture checks Contains null), so only its absence
    # is worth reporting.
    info = schema.EVALUATORS.get(evaluator_name or "")
    if info and info.value_kind != "none" and "value" not in condition:
        findings.append(
            _error(f"{where}.condition.value", f"Missing. {evaluator_name} needs something to compare against.")
        )

    tolerance = condition.get("error_tolerance")
    if tolerance is not None and not isinstance(tolerance, int):
        findings.append(
            _error(f"{where}.condition.error_tolerance", f"Must be an integer, not {type(tolerance).__name__}.")
        )


def _check_eval_expression(policy: Dict, declared_ids: List[str], findings: List[Finding]) -> None:
    expression = policy.get("eval_expression")
    if expression is None:
        findings.append(_error("eval_expression", "Missing. This combines the check ids into one verdict."))
        return
    if not isinstance(expression, str):
        findings.append(_error("eval_expression", f"Must be a string, not {type(expression).__name__}."))
        return
    if not expression.strip():
        findings.append(_error("eval_expression", "Empty. Name at least one check id."))
        return

    # core rejects & and | with a clear message; catch them here so the playground says so
    # before the engine runs at all.
    if re.search(r"(?<!&)&(?!&)", expression):
        findings.append(_error("eval_expression", "Use '&&' for and; a single '&' is not supported."))
    if re.search(r"(?<!\|)\|(?!\|)", expression):
        findings.append(_error("eval_expression", "Use '||' for or; a single '|' is not supported."))

    declared = set(declared_ids)
    referenced = set(_names_in_expression(expression, declared))

    for name in sorted(referenced - declared):
        # core strips undefined names and reports them, having already computed a verdict
        # without them, so the expression does not mean what it says. Worse if the name
        # contains a hyphen: nothing substitutes it, the `-` survives to the parser and the
        # engine raises ValueError instead of returning a result at all.
        if _ID_PATTERN.match(name):
            findings.append(
                _error(
                    "eval_expression",
                    f"'{name}' is not the id of any check; it will be dropped from the expression.",
                )
            )
        else:
            findings.append(
                _error(
                    "eval_expression",
                    f"'{name}' is not the id of any check, and because it is not a plain identifier "
                    f"the engine fails outright rather than dropping it.",
                )
            )
    for name in sorted(declared - referenced):
        findings.append(_warning("eval_expression", f"Check '{name}' runs but is not used in the expression."))


def _names_in_expression(expression: str, declared: set) -> List[str]:
    """
    The identifiers an eval_expression refers to.

    Mirrors what core actually does, which is *not* a parse. core substitutes each declared id
    into the string by regex (`\\bid\\b`) before compiling, so ids that are not valid Python
    names -- `eval-id-1`, used by several shipped policies -- are resolved fine when declared
    and only reach the parser when they are not. Parsing first would therefore read `eval-id-1`
    as `eval - id - 1` and report three phantom undefined names.

    So: remove the declared ids the same way core does, then read whatever identifier-ish
    tokens are left over as the undefined references.

    :param declared: Ids declared by the policy, removed before scanning for leftovers.
    """
    remaining = expression
    for check_id in sorted(declared, key=len, reverse=True):
        remaining = re.sub(r"\b" + re.escape(check_id) + r"\b", " ", remaining)

    names = [check_id for check_id in declared if re.search(r"\b" + re.escape(check_id) + r"\b", expression)]

    # Whatever still looks like a name is undefined. Hyphens are included so that a stray
    # `eval-id-9` is reported as one name rather than as `eval`, `id` and a number.
    for token in re.findall(r"[A-Za-z_][\w-]*", remaining):
        if token not in ("and", "or", "not", "True", "False", "None"):
            names.append(token)
    return names


def check_input_document(document: Any, provider_name: str) -> List[Finding]:
    """
    Sanity-check an input document against what the provider expects.

    Shallow by design: it reports the shape mistakes that produce a confusing empty result --
    a terraform plan with no `resource_changes`, an infracost report with no `projects` -- and
    says nothing about documents it has no expectations for.
    """
    findings: List[Finding] = []

    if provider_name == "stackguardian/terraform_plan":
        if not isinstance(document, dict):
            findings.append(_error("<input>", "A terraform plan is a JSON object."))
        elif not document.get("resource_changes"):
            findings.append(
                _warning(
                    "<input>.resource_changes",
                    "Absent or empty, so every check reports 'No Terraform resources changes are found'. "
                    "This should be the output of `terraform show -json`, not the binary plan.",
                )
            )
    elif provider_name == "stackguardian/infracost":
        if isinstance(document, dict) and "projects" not in document:
            findings.append(
                _warning(
                    "<input>.projects", "Absent, so cost lookups error. Expected `infracost breakdown --format json`."
                )
            )
    elif provider_name == "stackguardian/kubernetes":
        if isinstance(document, dict):
            findings.append(
                _warning(
                    "<input>",
                    "The kubernetes provider iterates a list of manifests; a single object will not match any kind.",
                )
            )

    return findings


def summarize(findings: List[Finding]) -> Tuple[int, int]:
    """Return (error count, warning count)."""
    errors = sum(1 for f in findings if f.severity == "error")
    return errors, len(findings) - errors
