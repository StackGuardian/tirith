---
id: infracost-provider
title: Infracost Provider
sidebar_label: Infracost
description: Reference for the stackguardian/infracost provider - operation types, parameters, return shapes, and error behavior.
keywords:
  - tirith
site_name: Tirith
slug: infracost-provider/
---

```
required_provider: stackguardian/infracost
```

Sums estimated costs from an Infracost cost breakdown, either for all resources or for a chosen set of resource types.

## Input document

The JSON produced by Infracost:

```bash
infracost breakdown --path . --format json > infracost.json
tirith -policy-path policy.json -input-path infracost.json
```

The provider reads `projects[].breakdown.resources[]` and understands both the older per-resource keys (`totalMonthlyCost` / `totalHourlyCost`) and the newer ones (`monthlyCost` / `hourlyCost`). Resources whose cost field is missing or `null` contribute nothing to the sum.

Note: only the **first** project in the `projects` array is summed.

## Operation types

| `operation_type` | Purpose |
|---|---|
| `total_monthly_cost` | Sum of estimated monthly costs |
| `total_hourly_cost` | Sum of estimated hourly costs |

Both operations take the same parameters:

| Parameter | Required | Description |
|---|---|---|
| `operation_type` | yes | `total_monthly_cost` or `total_hourly_cost`. |
| `resource_type` | yes | Which resources to sum. `"*"`, `["*"]`, or an empty value sums **all** resources. Otherwise, a list of Terraform resource type names (e.g. `["aws_eks_cluster", "aws_s3_bucket"]`); a resource is included when the type part of its name (everything before the first `.`) is in the list. |

**Returns:** a single number — the sum of the selected resources' costs. If nothing matches, the sum is `0`.

**On a miss / error:** all errors from this provider carry **no severity value**, so they always fail the check and `error_tolerance` cannot skip them:

- `operation_type` or `resource_type` key missing from `provider_args` — error `'resource_type/operation_type not found in provider_args'`.
- An `operation_type` other than the two above — error naming the unknown value.
- Input without a `projects` key — error `'projects not found in input_data'`.
- A project without `breakdown.resources` — error `'breakdown/resources not found in one of the project'`.

## Example

Verified end-to-end against the test fixtures — the total monthly cost of the stack must stay at or below 30, and the selected resource types must be free:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/infracost"
  },
  "evaluators": [
    {
      "id": "cost_check_1",
      "provider_args": {
        "operation_type": "total_monthly_cost",
        "resource_type": ["*"]
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 30
      }
    },
    {
      "id": "cost_check_2",
      "provider_args": {
        "operation_type": "total_monthly_cost",
        "resource_type": ["aws_eks_cluster", "aws_s3_bucket"]
      },
      "condition": {
        "type": "Equals",
        "value": 0
      }
    }
  ],
  "eval_expression": "cost_check_1 && cost_check_2"
}
```

Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md); CLI flags in the [CLI reference](../tirith-usage/cli-reference.md).
