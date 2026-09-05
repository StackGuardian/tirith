# Sentinel to Tirith

Measured, not estimated. Every table here was built by classifying the 110 policies in
`hashicorp/terraform-sentinel-policies` (AWS, Azure, GCP, VMware, cloud-agnostic) and
`hashicorp/policy-library-CIS-Policy-Set-for-AWS-Terraform`, then checking the Tirith side against
the engine.

## What to expect

| | exact | approximate | not expressible |
| --- | --- | --- | --- |
| All 110 | 41 | 40 | 29 |
| CIS AWS (32) | 13 | 14 | 5 |
| Cloud-specific (48) | 25 | 17 | 6 |
| Cloud-agnostic (30) | 3 | 9 | 18 |

Attribute policies on a single resource type translate exactly. The cloud-agnostic set is mostly
`tfconfig` and `tfrun` policies, which is why it does not.

## Imports

| Sentinel import | Tirith | Notes |
| --- | --- | --- |
| `tfplan/v2` | `stackguardian/terraform_plan` | The main path. Reads `resource_changes[].change.after` |
| `tfplan/v2` `terraform_version` | operation `terraform_version` | |
| `tfconfig/v2` provider blocks | operation `provider_config` | Only `region` (constant values) and `version_constraint`. Needs `terraform_provider_full_name` |
| `tfconfig/v2` anything else | none | Module sources and versions, variables, outputs, provisioners, expression references. Not expressible |
| `tfstate/v2` | `stackguardian/json` on a state file | `key_path` wildcards cannot filter by resource type, so other types are swept in |
| `tfrun.cost_estimate` | `stackguardian/infracost` | Different data source and different numbers; total only, no percentage increase |
| `tfrun.workspace`, `tfrun.variables`, `tfrun.is_destroy` | none | Not expressible |
| `http` | none | Not expressible |

## Common-function helpers

The `tfplan-functions` library is how most public policies are written. Each helper returns the
*violations*, so the Tirith condition is the desired state, which is the helper's opposite.

The fidelity column rates the **test**. The **scope** and the **attribute** can still make a
translation approximate: Sentinel skips no-op and deleted resources and Tirith does not (see
"Scope differs even when the test is exact"), and an attribute that is computed at apply time,
such as `region` on a bucket that inherits it from the provider, is absent from `change.after`
and fails in Tirith where the helper's absence-tolerant flag passed it in Sentinel (see "Unknown
values"). Check both before marking a row exact.

| Helper | Tirith condition | Fidelity |
| --- | --- | --- |
| `find_resources(type)` | `terraform_resource_type` | exact |
| `filter_attribute_is_value(a, v)` | `Equals v` | exact |
| `filter_attribute_is_not_value(a, v)` | `NotEquals v` | exact |
| `filter_attribute_not_in_list(a, allowed)` | `ContainedIn allowed` | exact |
| `filter_attribute_in_list(a, forbidden)` | `NotContainedIn forbidden` | exact |
| `filter_attribute_contains_items_from_list(a, forbidden)` | one `NotContains` evaluator per item, joined with `&&` | exact |
| `filter_attribute_contains_items_not_in_list(a, allowed)` | none: needs a subset test | not expressible |
| `filter_attribute_map_key_contains_items_not_in_list` | none: same | not expressible |
| `filter_attribute_greater_than_value(a, n)` | `LessThanEqualTo n` | exact |
| `filter_attribute_less_than_value(a, n)` | `GreaterThanEqualTo n` | exact |
| `filter_attribute_greater_than_equal_to_value(a, n)` | `LessThan n` | exact |
| `filter_attribute_less_than_equal_to_value(a, n)` | `GreaterThan n` | exact |
| `filter_attribute_does_not_match_regex(a, re)` | `RegexMatch re` | exact |
| `filter_attribute_matches_regex(a, re)` | `RegexMatch re` and `!` in the expression | exact |
| `filter_attribute_does_not_have_prefix(a, p)` | `RegexMatch "^p"` | exact |
| `filter_attribute_does_not_have_suffix(a, s)` | `RegexMatch "s$"` | exact |
| `case_insensitive_filter_...` | `RegexMatch "(?i)..."` | exact |
| `filter_attribute_was_value` | none: reads `change.before` | not expressible, issue #332 |
| `find_resources_being_destroyed()` | operation `action`, `NotEquals "delete"`, no negation | exact. `action` emits one result per action, so this fails on a replacement too. If the source excludes replacements, use `ContainedIn ["delete"]` with `!` instead |
| `find_providers_by_type` region checks | `provider_config`, `attribute: region` | approximate: a region set from a variable is invisible |
| `find_all_module_calls`, `get_module_source` | none | not expressible, issue #348 |
| `find_all_provisioners` | none | not expressible |
| `find_all_variables`, `find_all_outputs` | none | not expressible |
| `find_datasources` | `terraform_resource_type` | approximate: data sources read at plan time are absent from `resource_changes` |
| `limit_proposed_monthly_cost` | infracost `total_monthly_cost`, `LessThanEqualTo` | approximate: different estimator |
| `limit_cost_and_percentage_increase` | total only | percentage not expressible |

## Idioms in hand-written policies

| Sentinel | Tirith |
| --- | --- |
| `x is v`, `x == v` | `Equals` |
| `x is not v` | `NotEquals` |
| `x in [...]` | `ContainedIn` |
| `x not in [...]` | `NotContainedIn` |
| `list contains x` | `Contains` |
| `x matches "re"` | `RegexMatch` |
| `x is not null`, `x is defined` | `IsNotEmpty`. Handles both an absent key and an explicit `null` |
| `x else default` | `error_tolerance: 2` skips a resource whose `change.after` lacks the key. It does **not** cover `null`: `terraform show -json` renders an unset optional list such as `cidr_blocks` as `null`, and `Contains`/`NotContains` on `null` is a hard "unsupported data type" failure that no tolerance forgives. A rule with `source_security_group_id` instead of CIDRs is a false positive under a CIDR translation, and there is no workaround today |
| `x is null`, `x is empty` | `IsEmpty` |
| `<  <=  >  >=` | `LessThan  LessThanEqualTo  GreaterThan  GreaterThanEqualTo` |
| `keys(r.tags) contains "Owner"` | `Contains "Owner"` on the `tags` attribute. `Contains` on a map tests its keys |
| `all X as r { c }` | one evaluator: it fails if any resource fails |
| `any X as r { c }` | not expressible: no existential quantifier |
| `not any X as r { c }` | a detector evaluator and `!` in the expression |
| `rule_a and rule_b` | `a && b`. Exact only when each rule ranges over all resources independently |
| `length(violations) is 0` | the evaluator itself |
| `param name default v` | `{{ var.name }}` in the value, with `-var` or `-var-path` |
| enforcement level in `sentinel.hcl` | `meta.enforcement`, passed through to the result. The CLI treats every policy as hard-mandatory under `--fail-on-error` |

Two engine behaviours to know, both verified:

- A present-but-null attribute is **not** a missing attribute. `error_tolerance: 2` skips a
  resource without the key; `"kms_key_id": null` is evaluated as null. `IsNotEmpty` fails it
  cleanly; `Contains`, `NotContains`, `ContainedIn` and the ordering conditions fail it as an
  unsupported type, which reads like a violation.
- A value unknown until apply is absent from `change.after`. Sentinel policies that accept any
  reference (`kms_key_id = aws_kms_key.x.arn`) see a value; Tirith sees a missing attribute.

## Scope differs even when the test is exact

`find_resources` and the `actions contains "create" or "update"` idiom exclude no-op and deleted
resources. Tirith evaluates every `resource_changes` entry of the type, so an unchanged resource
that already violates the rule fails the plan (Sentinel passes it), and a deleted resource is a
severity-0 error that is skipped without touching its siblings' verdicts. This applies to every
row marked exact above: exact on the resources both tools evaluate, not on which resources are
evaluated.

## Why 69 of 110 are not exact

In order of how often each was the reason:

1. **Conditional scope and per-block conjunction** (about 20). "Ingress rules where type is
   ingress and from_port ≤ 22 ≤ to_port and cidr is 0.0.0.0/0" cannot bind the tests to one block.
   The translation is stricter. Issue #316, `resource_filter`, is the fix.
2. **Instance-level pairing across resources** (about 11). "Every bucket has a logging resource
   pointing at it." `direct_references` is type-level, so one compliant helper resource satisfies
   every bucket. Not tracked as an issue.
3. **`tfconfig`-only data** (about 14). Module sources and versions, provisioners, variables,
   provider version constraints. Issue #348, an HCL source provider, is research.
4. **Unknown values** (about 4). A `kms_key_id` referencing a key created in the same plan.
5. **`change.before` and destroys** (about 3). Issue #332.
6. **Cost percentage, workspace metadata, `http`** (about 7). Not planned.
7. **JSON documents inside strings** (2). IAM policy statements behind `jsonencode`. Issue #338.

## From a Sentinel mock to a Tirith fixture

Sentinel tests live in `test/<policy>/`. Each `*.hcl` there names a mock file and states the
expected verdict (`main = false` is the failing case); mock filenames vary, so read the `.hcl`
first. The
`resource_changes` map in a mock has the same keys as `terraform show -json`: `address`, `type`,
`name`, `mode`, `change.actions`, `change.before`, `change.after`, `change.after_unknown`.
Transcribe the failing mock to `should-fail.json` and the passing one to `should-pass.json`,
wrapped as `{"format_version": "1.2", "terraform_version": "...", "resource_changes": [...]}`.
Drop `tfconfig` and `tfstate` mocks; Tirith does not read them.

## Refusing well

When a policy is not expressible, the reader needs three sentences: what the policy enforces,
what Tirith cannot see, and what would change that. See
`examples/sentinel/require-private-registry-modules/notes.md` for the shape.
