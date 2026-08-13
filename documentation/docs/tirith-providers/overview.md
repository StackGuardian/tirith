---
id: providers-overview
title: Providers Overview
sidebar_label: Overview
description: What a Tirith provider is, how required_provider selects one, how provider_args are passed, and the list of available providers.
keywords:
  - tirith
site_name: Tirith
slug: providers-overview/
---

A **provider** is the part of Tirith that knows how to read one specific kind of input document and extract values from it. The policy declares which provider to use; each evaluator in the policy then asks the provider for values (via `provider_args`), and the evaluator's `condition` is applied to every value the provider returns.

## Selecting a provider

The provider is selected once for the whole policy with `meta.required_provider`:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [ ... ],
  "eval_expression": "..."
}
```

The value must be one of the exact strings below. If the string does not match any known provider, every evaluator in the policy fails with an error.

| `required_provider` | Summary | Expected input document |
|---|---|---|
| [`stackguardian/terraform_plan`](terraform-plan.md) | Inspects resource changes, actions, counts, dependencies, references, provider configuration, and the Terraform version in a Terraform plan. | Terraform plan in JSON form (`terraform show -json <plan-file>`) |
| [`stackguardian/infracost`](infracost.md) | Sums estimated monthly or hourly costs from an Infracost breakdown. | Infracost output (`infracost breakdown --format json`) |
| [`stackguardian/json`](json.md) | Extracts values from any JSON or YAML document by key path, with wildcard support. | Any JSON or YAML file |
| [`stackguardian/kubernetes`](kubernetes.md) | Extracts attribute values from Kubernetes manifests of a given `kind`. | A list of Kubernetes manifests (multi-document YAML, e.g. `helm template` output) |
| [`stackguardian/sg_workflow`](sg-workflow.md) | Reads attributes of a StackGuardian workflow definition. | StackGuardian workflow JSON |

## How `provider_args` reaches the provider

Each evaluator carries a `provider_args` object. Tirith hands that object to the selected provider **verbatim** — the provider decides which keys it understands. Every provider except `stackguardian/sg_workflow` dispatches on the `operation_type` key; the remaining keys are parameters of that operation.

```json
{
  "id": "my_check",
  "provider_args": {
    "operation_type": "attribute",
    "terraform_resource_type": "aws_s3_bucket",
    "terraform_resource_attribute": "force_destroy"
  },
  "condition": {
    "type": "Equals",
    "value": false
  }
}
```

The provider returns a **list of results**. Each result is a value extracted from the input (a scalar, a list, or a dict, depending on the operation). The evaluator's `condition` is applied to each value independently, and the evaluator passes only if **every** value passes. If the provider returns nothing at all, the evaluator fails with the message `Could not find input value`.

For the available condition types (`Equals`, `Contains`, `RegexMatch`, ...) see the [evaluators reference](../tirith-reference/evaluators.md).

## How the input document is parsed

The file given to [`-input-path`](../tirith-usage/cli-reference.md) is parsed by extension:

- `.yaml` / `.yml` — parsed as YAML. A file with multiple documents (separated by `---`) becomes a **list** of documents; a file with a single document becomes that document directly.
- anything else — parsed as JSON.

The parsed value is what the provider sees.

## Errors, misses, and `error_tolerance`

When a provider cannot find what an operation asked for, it reports an error instead of a value. There are two kinds:

1. **Errors with a severity value.** Most "not found" situations carry a numeric severity. Whether the check fails or is skipped depends on the evaluator's `condition.error_tolerance` (default `0`):
   - severity **greater than** `error_tolerance` — the check **fails**.
   - severity **less than or equal to** `error_tolerance` — the check is **skipped** (its `passed` is `null`, and its id is dropped from `eval_expression`).

   The conventional severity values are:

   | Severity | Meaning |
   |---|---|
   | 0 | Nothing to inspect (e.g. no resource changes in the plan). Skipped even at the default tolerance. |
   | 1 | The requested resource / kind / provider was not found. |
   | 2 | The resource was found but the requested attribute / key path was not. |
   | 99 | The `provider_args` themselves are invalid (unsupported operation, missing required parameter). Practically never tolerated. |

2. **Errors without a severity value.** Some errors (an unsupported `operation_type` in the `json` and `kubernetes` providers, and all errors from the `infracost` and `sg_workflow` providers) carry no severity. These always **fail** the check, regardless of `error_tolerance`.

Each provider page below lists exactly which situation produces which severity. See also [error tolerance](../tirith-policies/tirith-policy-error-tolerance.md).
