# Schema — the closed vocabulary

Both registries are closed. Inventing a value does not raise an error: an unknown
`condition.type` reaches the engine as an **ordinary failed check with no error attached**, so it
is indistinguishable from a real violation and sends someone to debug infrastructure that is fine.

Confirm against the live registry rather than this file. It is the source of truth:

```bash
python -c "from tirith.core.evaluators import EVALUATORS_DICT; print(sorted(EVALUATORS_DICT))"
```

## Policy shape

| Key | Required | Notes |
| --- | --- | --- |
| `meta.version` | yes | `"v1"` |
| `meta.required_provider` | yes | One of the providers below |
| `meta.name` / `description` / `severity` / `tags` | no | Passed through to the result document |
| `evaluators[]` | yes | Each needs `id`, `provider_args`, `condition` |
| `eval_expression` | yes | Combines evaluator ids with `&&`, `\|\|`, `!`, parentheses |

## Condition types — all 13

```
ContainedIn   Contains   Equals   GreaterThan   GreaterThanEqualTo   IsEmpty
IsNotEmpty    LessThan   LessThanEqualTo   NotContainedIn   NotContains
NotEquals     RegexMatch
```

There is no `Exists`, no `Matches`, no `In`, and no `NotRegexMatch`. Use `IsNotEmpty` for
presence, and `!` in `eval_expression` for negation.

`condition.value` keeps its JSON type: `true` and `"true"` are different questions.

## Providers and operations

| `required_provider` | Reads | `operation_type` |
| --- | --- | --- |
| `stackguardian/terraform_plan` | `terraform show -json` output | `action`, `attribute`, `count`, `direct_dependencies`, `direct_references`, `provider_config`, `terraform_version` |
| `stackguardian/kubernetes` | Kubernetes manifests (YAML or JSON) | `attribute` |
| `stackguardian/infracost` | An Infracost breakdown | `total_monthly_cost`, `total_hourly_cost` |
| `stackguardian/json` | Any JSON document, including a Terraform state file | `get_value` |
| `stackguardian/sg_workflow` | A StackGuardian workflow definition | `attribute` |

## The argument key differs per provider

This is the highest-cost mistake in the schema, because the wrong key is **ignored rather than
rejected** — the evaluator then reads nothing and the check does not measure what you think.

| Provider | Key naming the value | Also needs |
| --- | --- | --- |
| `terraform_plan` | `terraform_resource_attribute` | `terraform_resource_type` (`"*"` = all) |
| `kubernetes` | `attribute_path` | `kubernetes_kind` |
| `json` | `key_path` | — |
| `sg_workflow` | `workflow_attribute` | — |

Paths are dot-separated and accept `*` as a wildcard across a list: `spec.containers.*.image`.

## `error_tolerance`

Lives **inside `condition`**. Anywhere else it has no effect. It forgives *problems reading the
input*, not policy failures, and the severities are specific:

| Severity | Means | Forgiven by |
| --- | --- | --- |
| `0` | The resource is being deleted (`change.after` is null) | `error_tolerance: 0` (the default forgives nothing) |
| `1` | The resource type is absent from the document | `error_tolerance: 1` or higher |
| `2` | The attribute is absent from the resource | `error_tolerance: 2` |

A forgiven problem makes the check **skipped**, not passed. A skipped check is removed from
`eval_expression` before evaluation. If every check is skipped the policy reports
`final_result: null` — see `reference/verdicts.md`.

## Not supported, despite appearances

`jmespath` and `jq_query` appear in some repository test fixtures. Neither ships. The `json`
provider supports `get_value`.
