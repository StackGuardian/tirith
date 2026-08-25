---
name: tirith-policies
description: Author, debug and review Tirith IaC governance policies. Use when writing or editing files under .tirith/policies, when a Tirith check fails in CI, when asked to add a guardrail to a Terraform or OpenTofu pipeline, or when reading a Tirith result document or exit code.
---

# Writing Tirith policies

A Tirith policy is **JSON data, not a program**. It names a provider, the value to inspect and
the condition that value must satisfy. Tirith does the traversal and returns resource-level
evidence.

Policies live under `.tirith/policies` and are evaluated against the plan a pipeline already
produces (`terraform show -json tfplan > plan.json`).

## Do not guess the vocabulary

The two mistakes that cost the most time are inventing a `condition.type` and inventing an
`operation_type`. Both are enumerated below. An unknown condition type is especially expensive:
**the engine reports it as an ordinary failed check with no error attached**, so it is
indistinguishable from a real violation and will send someone to debug infrastructure that is
fine.

If the `mcp` extra is installed, prefer the tools over this file — they read the live registries:

```
tirith mcp        # describe_provider, lint_policy, evaluate, explain_result
```

## Shape

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "name": "Every resource carries a costcenter tag"
  },
  "evaluators": [{
    "id": "costcenter_tag_present",
    "description": "Every taggable resource declares a costcenter tag",
    "provider_args": {
      "operation_type": "attribute",
      "terraform_resource_type": "*",
      "terraform_resource_attribute": "tags.costcenter"
    },
    "condition": {"type": "IsNotEmpty"}
  }],
  "eval_expression": "costcenter_tag_present"
}
```

- `eval_expression` references evaluators **by id** and combines them with `and` / `or`. An
  evaluator the expression never names cannot affect the verdict.
- `terraform_resource_type: "*"` means every resource type is in scope.

## Condition types

`ContainedIn`, `Contains`, `Equals`, `GreaterThan`, `GreaterThanEqualTo`, `IsEmpty`,
`IsNotEmpty`, `LessThan`, `LessThanEqualTo`, `NotContainedIn`, `NotContains`, `NotEquals`,
`RegexMatch`

There is no `Exists`, no `Matches`, no `In`. Use `IsNotEmpty` for presence.

## Providers and their `operation_type` values

| `required_provider` | Reads | `operation_type` |
|---|---|---|
| `stackguardian/terraform_plan` | a `terraform show -json` plan | `action`, `attribute`, `count`, `direct_dependencies`, `direct_references`, `provider_config`, `terraform_version` |
| `stackguardian/infracost` | an Infracost breakdown | `total_monthly_cost`, `total_hourly_cost` |
| `stackguardian/kubernetes` | Kubernetes manifests | `attribute` |
| `stackguardian/json` | any JSON document | `get_value` |
| `stackguardian/terraform_state` | a state document | as for plans |

## Gotchas the schema does not tell you

Each of these produces a policy that looks correct and behaves wrongly. They cost real time to
discover.

- **The key naming the value to read differs per provider.** `terraform_plan` and
  `terraform_state` use `terraform_resource_attribute`; `kubernetes` uses `attribute_path` (and
  requires `kubernetes_kind`); `json` uses `key_path`. Using another provider's key is not an
  error — it is *ignored*, so the evaluator reads `None` and tests the condition against nothing.
- **`error_tolerance` lives inside `condition`**, and its severities are specific:
  `0` = the resource is being deleted (`change.after` is null), `1` = the type is absent from the
  plan, `2` = the attribute is absent. Choose the tolerance from which of those you mean to
  forgive, not by feel.
- **There is no `NotRegexMatch`**, and no inverse conditions generally. Write the positive
  detector and invert it in `eval_expression` with `!`. That is the only negation mechanism.
- **`operation_type: attribute` reads `change.after` only.** Nothing about a resource being
  *destroyed* is visible through it — use `action` for that.
- **`count` has no action filter**, and Terraform reports unchanged resources as `no-op`, so
  `count(*)` measures root-module size, not the size of the change. Blast radius is not
  expressible today.
- **`jmespath` and `jq_query` do not ship.** Some test fixtures in the repository reference them,
  which makes them look supported. The `json` provider supports `get_value`.

## Reading the verdict

Exit codes are a contract. Never collapse them:

| Exit | Meaning |
|---|---|
| `0` | Policies passed, or nothing was in scope |
| `3` | A policy ran and said no — the change violates a rule |
| `1` | Tirith could not tell you either way: bad input, an unevaluable policy, or **every check skipped** |

`final_result: null` means every check was skipped. **That is not a pass.** It almost always
means `provider_args` matched nothing — check `terraform_resource_type` and the attribute path
before touching the condition.

One asymmetry worth knowing: when a check fails because an attribute is *absent*, there is no
value to attach a resource to, so that failure arrives **without a resource address**. Find the
culprit by looking in the plan for the resource lacking the attribute.

## Before you hand a policy back

1. Does `eval_expression` reference every evaluator you wrote?
2. Is every `condition.type` in the list above?
3. Did you **run it**? A policy that matches nothing looks identical to one that works.

```bash
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

Never claim a policy works without evaluating it against a document that should fail it. A
guardrail only ever seen passing is a guardrail nobody has tested.

## Reference

- Policy reference — https://stackguardian.github.io/tirith/docs/tirith-policies/tirith-policy-reference/
- Conditions — https://stackguardian.github.io/tirith/docs/tirith-policies/tirith-policy-conditions/
- Exit codes — https://stackguardian.github.io/tirith/docs/tirith-usage/exit-codes/
- Worked examples — `src/tirith/tui/examples/`
