"""
The four tools, as plain functions.

Deliberately free of any MCP import: the protocol layer in server.py adapts these, and keeping
them separate means the behaviour can be tested on Python 3.8 where the SDK cannot even be
installed. It also means the same functions are callable from anything else that wants them.

Every tool returns a JSON-serialisable dict. None of them touch the network, and none of them
write to disk -- an agent operating on someone's infrastructure repository should not be able to
cause a change by asking a question.
"""

from typing import Any, Dict, List, Optional

from ..core.core import start_policy_evaluation_from_dict
from ..core.evaluators import EVALUATORS_DICT

# What each provider accepts as `operation_type`.
#
# Read from the providers themselves wherever they keep a registry, so this cannot drift: json
# and kubernetes both expose SUPPORTED_OPS. terraform_plan dispatches through an if/elif chain
# with no registry to import, so its operations are listed here and guarded by a test that reads
# the handler source -- see tests/mcp/test_tools.py.
_TERRAFORM_PLAN_OPS = [
    "action",
    "attribute",
    "count",
    "direct_dependencies",
    "direct_references",
    "provider_config",
    "terraform_version",
]


# Which provider_args key names the value to read. Each provider chose its own, so a key that is
# correct for one is silently ignored by another -- and an ignored key means the evaluator reads
# None and tests the condition against nothing.
_ATTRIBUTE_KEY = {
    "terraform_plan": "terraform_resource_attribute",
    "terraform_state": "terraform_resource_attribute",
    "kubernetes": "attribute_path",
    "json": "key_path",
}


def _operations_for(name):
    if name == "terraform_plan":
        return list(_TERRAFORM_PLAN_OPS)
    if name == "json":
        from ..providers.json import handler as json_handler

        return sorted(json_handler.SUPPORTED_OPS)
    if name == "kubernetes":
        from ..providers.kubernetes import handler as k8s_handler

        return sorted(k8s_handler.SUPPORTED_OPS)
    if name == "infracost":
        return ["total_monthly_cost", "total_hourly_cost"]
    return []


def _exit_code_for(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    The `--fail-on-error` exit contract, as data.

    Duplicated from the CLI's decision rather than imported because the CLI decides this while
    also handling flags, printing and process exit; what a tool caller needs is only the mapping
    from a tri-state final_result to the code a pipeline would see -- and the sentence explaining
    it, which is the part an agent gets wrong.
    """
    if "final_result" not in result:
        return {
            "exit_code": 1,
            "outcome": "errored",
            "meaning": "The policy could not be evaluated at all. This is not a policy failure.",
        }
    final = result.get("final_result")
    if final is True:
        return {"exit_code": 0, "outcome": "passed", "meaning": "Every check that ran passed."}
    if final is False:
        return {
            "exit_code": 3,
            "outcome": "failed",
            "meaning": "A check ran and failed. With --fail-on-error this stops the job.",
        }
    return {
        "exit_code": 1,
        "outcome": "unevaluated",
        "meaning": (
            "Every check was skipped, so the policy evaluated nothing. This is NOT a pass -- "
            "it usually means the provider matched no resources, or error_tolerance swallowed a "
            "provider error."
        ),
    }


# Things the schema does not tell you, each of which produces a policy that looks correct and
# behaves wrongly. Returned by describe_provider so an agent gets them before writing, rather
# than discovering them one confusing verdict at a time.
GOTCHAS = [
    "The key that names the value to read differs per provider: terraform_plan and "
    "terraform_state use `terraform_resource_attribute`, kubernetes uses `attribute_path` (with "
    "`kubernetes_kind`), json uses `key_path`. Using the wrong one is not an error -- the key is "
    "ignored, so the evaluator reads None and tests the condition against nothing.",
    "`error_tolerance` lives inside `condition`. Its severities are specific: 0 = the resource is "
    "being deleted (`change.after` is null), 1 = the type is absent from the plan, 2 = the "
    "attribute is absent. Choose the tolerance from which of those you mean to forgive.",
    "There is no NotRegexMatch, and no inverse conditions generally. Write the positive detector "
    "and invert it in `eval_expression` with `!`.",
    "`operation_type: attribute` reads `change.after` only. Nothing about a resource being "
    "destroyed is visible through it -- use `action` for that.",
    "`count` has no action filter, and Terraform reports unchanged resources as `no-op`, so "
    "`count(*)` measures root-module size rather than the size of the change.",
    "`jmespath` and `jq_query` do not ship, despite appearing in some test fixtures. The json "
    "provider supports `get_value`.",
]


def evaluate(policy: Dict[str, Any], document: Any, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a policy against an input document and return the real verdict.

    This is the tool that stops an agent guessing. A policy that looks correct and matches
    nothing is indistinguishable from one that works until you run it, so the honest answer to
    "is this policy right?" is always to evaluate it.
    """
    result = start_policy_evaluation_from_dict(policy, document, variables or {})
    verdict = _exit_code_for(result)
    return {
        "verdict": verdict,
        "result": result,
        "note": (
            "`unevaluated` is not a pass. If you expected resources to be checked and none were, "
            "the provider_args are matching nothing -- check terraform_resource_type and the "
            "attribute path before changing the condition."
        ),
    }


def lint_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check a policy's shape before it is ever run.

    Catches the mistakes that produce a confusing verdict rather than an error: a missing
    eval_expression, an evaluator id the expression never references, a condition type the engine
    does not implement. The engine reports several of these as an ordinary failed check with no
    error attached -- indistinguishable from a real violation -- so finding them here is the
    difference between "your policy is wrong" and "your infrastructure is wrong".
    """
    problems: List[Dict[str, str]] = []

    def fail(field, message):
        problems.append({"severity": "error", "field": field, "message": message})

    def warn(field, message):
        problems.append({"severity": "warning", "field": field, "message": message})

    if not isinstance(policy, dict):
        return {"ok": False, "problems": [{"severity": "error", "field": ".", "message": "Policy must be a JSON object."}]}

    meta = policy.get("meta")
    if not isinstance(meta, dict):
        fail("meta", "Missing `meta` object.")
    else:
        if not meta.get("required_provider"):
            fail("meta.required_provider", "Missing. Name the provider this policy reads, e.g. 'stackguardian/terraform_plan'.")
        if not meta.get("name"):
            warn("meta.name", "No name. The name is what appears in the verdict, so an unnamed policy is hard to act on.")
        if not meta.get("version"):
            warn("meta.version", "No version. 'v1' is the current schema version.")

    provider_name = ""
    if isinstance(meta, dict):
        provider_name = (meta.get("required_provider") or "").split("/")[-1]

    evaluators = policy.get("evaluators")
    ids = []
    if not isinstance(evaluators, list) or not evaluators:
        fail("evaluators", "Missing or empty. A policy needs at least one evaluator.")
    else:
        for index, evaluator in enumerate(evaluators):
            where = f"evaluators[{index}]"
            if not isinstance(evaluator, dict):
                fail(where, "Each evaluator must be an object.")
                continue
            eid = evaluator.get("id")
            if not eid:
                fail(f"{where}.id", "Missing id. The eval_expression refers to evaluators by id.")
            else:
                if eid in ids:
                    fail(f"{where}.id", f"Duplicate id '{eid}'. Ids must be unique within a policy.")
                ids.append(eid)
            args = evaluator.get("provider_args")
            if not isinstance(args, dict):
                fail(f"{where}.provider_args", "Missing provider_args. This is what selects the values to test.")
            else:
                operation = args.get("operation_type")
                if not operation:
                    fail(f"{where}.provider_args.operation_type", "Missing operation_type.")
                elif operation in ("jmespath", "jq_query"):
                    # A test fixture in this repository uses these, which makes them look
                    # supported. They are not: the json provider's SUPPORTED_OPS is {"get_value"}
                    # and there is no jq dependency anywhere.
                    fail(
                        f"{where}.provider_args.operation_type",
                        f"'{operation}' does not ship. Some test fixtures reference it, which is "
                        "misleading. Use 'get_value' for the json provider.",
                    )
                # A key belonging to a different provider is the trap: it is not rejected,
                # it is ignored.
                expected = _ATTRIBUTE_KEY.get(provider_name)
                if expected:
                    foreign = [k for k in set(_ATTRIBUTE_KEY.values()) if k != expected and k in args]
                    for key in sorted(foreign):
                        fail(
                            f"{where}.provider_args.{key}",
                            f"'{key}' belongs to a different provider. {provider_name} reads "
                            f"'{expected}'. An unrecognised key is ignored rather than rejected, "
                            "so the evaluator would read None and test the condition against "
                            "nothing.",
                        )
                if provider_name == "kubernetes" and operation == "attribute" and not args.get("kubernetes_kind"):
                    fail(
                        f"{where}.provider_args.kubernetes_kind",
                        "The kubernetes provider requires kubernetes_kind alongside attribute_path.",
                    )
                if "error_tolerance" in args:
                    warn(
                        f"{where}.provider_args.error_tolerance",
                        "error_tolerance belongs inside `condition`, not in provider_args, where "
                        "it has no effect.",
                    )
            if "error_tolerance" in evaluator:
                warn(
                    f"{where}.error_tolerance",
                    "error_tolerance belongs inside `condition`, not on the evaluator.",
                )
            condition = evaluator.get("condition")
            if not isinstance(condition, dict):
                fail(f"{where}.condition", "Missing condition object.")
            elif not condition.get("type"):
                fail(f"{where}.condition.type", "Missing condition type.")
            elif condition["type"] == "NotRegexMatch":
                fail(
                    f"{where}.condition.type",
                    "There is no NotRegexMatch. Write the positive detector with RegexMatch and "
                    "invert it in eval_expression with '!' -- that is the only negation mechanism.",
                )
            elif condition["type"] not in EVALUATORS_DICT:
                # The highest-value lint here. An unsupported condition type comes back from the
                # engine as an ordinary failed check with no error attached -- indistinguishable
                # from a real violation -- so it fails closed while pointing at the user's
                # infrastructure when the fault is in the policy. Catching it before the run is
                # the difference between a confusing red build and a fixed typo.
                fail(
                    f"{where}.condition.type",
                    f"'{condition['type']}' is not a condition type. The engine reports an unknown "
                    "type as an ordinary failed check, so this would look like a real violation. "
                    "Available: " + ", ".join(sorted(EVALUATORS_DICT)),
                )

    expression = policy.get("eval_expression")
    if not expression:
        fail("eval_expression", "Missing. Name which evaluators must pass, e.g. 'a and b'.")
    elif isinstance(expression, str) and ids:
        unreferenced = [i for i in ids if i not in expression]
        if unreferenced:
            warn(
                "eval_expression",
                "These evaluator ids are never referenced, so they cannot affect the verdict: "
                + ", ".join(unreferenced),
            )

    return {"ok": not any(p["severity"] == "error" for p in problems), "problems": problems}


def describe_provider(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    What a policy is allowed to say.

    An agent that has not been told the vocabulary invents plausible-looking values --
    `operation_type: "tag"`, `condition.type: "Exists"` -- which the engine either rejects or,
    worse, treats as an ordinary failing check. Reading the real registries is cheaper than
    debugging that.
    """
    conditions = sorted(EVALUATORS_DICT)

    providers = {
        "terraform_plan": "A `terraform show -json` plan. The main surface: gate a change before apply.",
        "terraform_state": "A state document, for auditing what is deployed rather than what is proposed.",
        "infracost": "An Infracost breakdown, for gating on monthly or hourly cost.",
        "kubernetes": "Kubernetes manifests.",
        "json": "Any JSON document, when nothing more specific fits.",
        "sg_workflow": "A StackGuardian workflow definition.",
    }

    if provider:
        key = provider.split("/")[-1]
        if key not in providers:
            return {"error": f"Unknown provider '{provider}'.", "known_providers": sorted(providers)}
        operations = _operations_for(key)
        return {
            "provider": f"stackguardian/{key}",
            "reads": providers[key],
            "operation_types": operations or "See the documentation link; this provider's operations are not enumerated here.",
            "condition_types": conditions,
            "docs": f"https://stackguardian.github.io/tirith/docs/tirith-providers/{key.replace('_', '-')}-provider/",
        }

    return {
        "providers": [
            {"name": f"stackguardian/{k}", "reads": v, "operation_types": _operations_for(k)}
            for k, v in sorted(providers.items())
        ],
        "condition_types": conditions,
        "gotchas": GOTCHAS,
        "note": "Call again with a provider name for its documentation link.",
    }


def explain_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Turn a result document into the sentence a human needs.

    The raw result is nested and repetitive; what someone actually wants is which rule failed, on
    which resource, and what value caused it. One caveat this surfaces honestly: when a check
    fails because an attribute is *absent*, the engine has no value to attach a resource to, so
    that failure arrives without an address. Saying so is more useful than pretending otherwise.
    """
    verdict = _exit_code_for(result)
    failures = []
    missing_address = 0

    for evaluator in result.get("evaluators", []) or []:
        for item in evaluator.get("result", []) or []:
            if item.get("passed") is not False:
                continue
            meta = item.get("meta") or {}
            address = meta.get("address")
            if not address:
                missing_address += 1
            failures.append(
                {
                    "rule": evaluator.get("description") or evaluator.get("id"),
                    "evaluator_id": evaluator.get("id"),
                    "resource": address,
                    "actions": (meta.get("change") or {}).get("actions"),
                    "message": item.get("message"),
                }
            )

    summary = f"{verdict['outcome']}: {verdict['meaning']}"
    if failures:
        summary += f" {len(failures)} failing check{'' if len(failures) == 1 else 's'}."

    out = {
        "policy": (result.get("meta") or {}).get("name"),
        "verdict": verdict,
        "failures": failures,
        "summary": summary,
    }
    if missing_address:
        out["note"] = (
            f"{missing_address} failing check(s) carry no resource address. That happens when the "
            "attribute is absent -- there is no value to attach a resource to -- so find the "
            "culprit by looking in the input document for the resource lacking that attribute."
        )
    return out
