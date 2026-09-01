# Policy Cookbook

Source: https://stackguardian.github.io/tirith/docs/tirith-policies/tirith-policy-cookbook/
Summary: Complete, runnable Tirith policies for common real-world checks, each shown with its input and the verdict it produces.

Every recipe on this page is complete: copy the policy and the input into files, run the command shown, and you will get the output shown. All commands use `--fail-on-error` so the exit code carries the verdict — `0` pass, `3` fail, `1` when the run could not produce a verdict (see the [exit code table](./tirith-policy-reference.md#outcomes-and-exit-codes) and the [CLI reference](../tirith-usage/cli-reference.md)).

Field-by-field schema details are in the [Policy Reference](./tirith-policy-reference.md); condition semantics in the [evaluator reference](../tirith-reference/evaluators.md); provider operations in the [provider documentation](../tirith-providers/overview.md).

## Forbid unapproved instance types

Every `aws_instance` in a Terraform plan must use an instance type from an approved list. `ContainedIn` checks each extracted value against the list, and the check passes only if **all** instances pass — so one oversized instance fails the whole policy.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "id": "allowed-instance-types",
    "name": "Only approved EC2 instance types",
    "description": "Every aws_instance in the plan must use an instance type from the approved list.",
    "severity": "HIGH"
  },
  "evaluators": [
    {
      "id": "instance_type_is_approved",
      "description": "aws_instance.instance_type must be one of the approved types",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_instance",
        "terraform_resource_attribute": "instance_type"
      },
      "condition": {
        "type": "ContainedIn",
        "value": ["t3.micro", "t3.small", "t3.medium"]
      }
    }
  ],
  "eval_expression": "instance_type_is_approved"
}
```

The input is a Terraform plan in JSON form (`terraform show -json plan.out > input.json`). This trimmed-down plan has one compliant and one non-compliant instance:

```json
{
  "format_version": "1.2",
  "terraform_version": "1.5.7",
  "resource_changes": [
    {
      "address": "aws_instance.web",
      "type": "aws_instance",
      "name": "web",
      "change": {
        "actions": ["create"],
        "after": {
          "instance_type": "t3.small",
          "tags": { "Environment": "prod" }
        }
      }
    },
    {
      "address": "aws_instance.batch",
      "type": "aws_instance",
      "name": "batch",
      "change": {
        "actions": ["create"],
        "after": {
          "instance_type": "m5.24xlarge",
          "tags": { "Environment": "prod" }
        }
      }
    }
  ]
}
```

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json
```

```text
Check: instance_type_is_approved
  FAILED
    1. PASSED: Found `"t3.small"` inside `["t3.medium", "t3.micro", "t3.small"]`
    2. FAILED: Failed to find `"m5.24xlarge"` inside `["t3.medium", "t3.micro", "t3.small"]`

Passed: 0 Failed: 1 Skipped: 0

Final expression used:
-> instance_type_is_approved
✘ Failed final evaluation
```

Exit code: `3`.

## Require an Environment tag on every resource

With `terraform_resource_type` set to `"*"`, the check runs against every resource in the plan. The dotted attribute path reaches into the `tags` map, and `RegexMatch` restricts the value to an allowed set.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "id": "require-environment-tag",
    "name": "Every resource carries an Environment tag",
    "description": "Every resource in the plan must be tagged with Environment set to dev, staging, or prod."
  },
  "evaluators": [
    {
      "id": "environment_tag_is_valid",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "*",
        "terraform_resource_attribute": "tags.Environment"
      },
      "condition": {
        "type": "RegexMatch",
        "value": "^(dev|staging|prod)$"
      }
    }
  ],
  "eval_expression": "environment_tag_is_valid"
}
```

```json
{
  "format_version": "1.2",
  "terraform_version": "1.5.7",
  "resource_changes": [
    {
      "address": "aws_s3_bucket.artifacts",
      "type": "aws_s3_bucket",
      "name": "artifacts",
      "change": {
        "actions": ["create"],
        "after": {
          "bucket": "team-artifacts",
          "tags": { "Environment": "prod" }
        }
      }
    },
    {
      "address": "aws_instance.web",
      "type": "aws_instance",
      "name": "web",
      "change": {
        "actions": ["create"],
        "after": {
          "instance_type": "t3.small",
          "tags": { "Environment": "staging" }
        }
      }
    }
  ]
}
```

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json
```

```text
Check: environment_tag_is_valid
  PASSED
    1. PASSED: `"prod"` matches regex pattern `"^(dev|staging|prod)$"`
    2. PASSED: `"staging"` matches regex pattern `"^(dev|staging|prod)$"`

Passed: 1 Failed: 0 Skipped: 0

Final expression used:
-> environment_tag_is_valid
✔ Passed final evaluator
```

Exit code: `0`.

A resource with no `tags.Environment` at all fails rather than slipping through. Against an input whose only resource has no tags:

```text
Check: environment_tag_is_valid
  FAILED
    1. FAILED: attribute: 'tags.Environment' is not found

Passed: 0 Failed: 1 Skipped: 0

Final expression used:
-> environment_tag_is_valid
✘ Failed final evaluation
```

Exit code: `3`. (A missing attribute is a severity-2 provider error; the default `error_tolerance` of 0 turns it into a failure. The [last recipe](#tolerate-a-missing-key) shows how to skip instead.)

## Block security group ingress from 0.0.0.0/0

A public-ingress check. The attribute path `ingress.*.cidr_blocks` extracts the `cidr_blocks` list of **each** ingress rule, and `NotContains` requires that none of those lists contain `0.0.0.0/0`.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "id": "no-public-ingress",
    "name": "No security group ingress from 0.0.0.0/0",
    "description": "No ingress rule of any aws_security_group may allow traffic from 0.0.0.0/0.",
    "severity": "HIGH",
    "remediation": "Restrict the CIDR range or reference another security group instead."
  },
  "evaluators": [
    {
      "id": "no_public_cidr_in_ingress",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_security_group",
        "terraform_resource_attribute": "ingress.*.cidr_blocks"
      },
      "condition": {
        "type": "NotContains",
        "value": "0.0.0.0/0"
      }
    }
  ],
  "eval_expression": "no_public_cidr_in_ingress"
}
```

```json
{
  "format_version": "1.2",
  "terraform_version": "1.5.7",
  "resource_changes": [
    {
      "address": "aws_security_group.web",
      "type": "aws_security_group",
      "name": "web",
      "change": {
        "actions": ["create"],
        "after": {
          "name": "web-sg",
          "ingress": [
            {
              "from_port": 443,
              "to_port": 443,
              "protocol": "tcp",
              "cidr_blocks": ["10.0.0.0/8"]
            },
            {
              "from_port": 22,
              "to_port": 22,
              "protocol": "tcp",
              "cidr_blocks": ["0.0.0.0/0"]
            }
          ]
        }
      }
    }
  ]
}
```

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json
```

```text
Check: no_public_cidr_in_ingress
  FAILED
    1. PASSED: Did not find 0.0.0.0/0 inside ['10.0.0.0/8']
    2. FAILED: Found `"0.0.0.0/0"` inside `["0.0.0.0/0"]`

Passed: 0 Failed: 1 Skipped: 0

Final expression used:
-> no_public_cidr_in_ingress
✘ Failed final evaluation
```

Exit code: `3`. The port-443 rule scoped to `10.0.0.0/8` passes; the SSH rule open to the world fails the policy.

## Cap the estimated monthly cost

Uses the `stackguardian/infracost` provider against an [Infracost](https://www.infracost.io/) breakdown (`infracost breakdown --path . --format json > input.json`). The `total_monthly_cost` operation sums the monthly cost of the matched resources; `["*"]` matches all of them.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/infracost",
    "id": "monthly-cost-ceiling",
    "name": "Monthly cost stays under the ceiling",
    "description": "The estimated total monthly cost of all resources must not exceed 500 USD."
  },
  "evaluators": [
    {
      "id": "total_monthly_cost_under_ceiling",
      "provider_args": {
        "operation_type": "total_monthly_cost",
        "resource_type": ["*"]
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 500
      }
    }
  ],
  "eval_expression": "total_monthly_cost_under_ceiling"
}
```

```json
{
  "version": "0.2",
  "currency": "USD",
  "projects": [
    {
      "name": "main",
      "breakdown": {
        "resources": [
          {
            "name": "aws_instance.web",
            "monthlyCost": "301.44"
          },
          {
            "name": "aws_db_instance.app",
            "monthlyCost": "109.86"
          },
          {
            "name": "aws_s3_bucket.artifacts",
            "monthlyCost": "2.30"
          }
        ]
      }
    }
  ]
}
```

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json
```

```text
Check: total_monthly_cost_under_ceiling
  PASSED
    1. PASSED: `413.6` is less than equal to `500`

Passed: 1 Failed: 0 Skipped: 0

Final expression used:
-> total_monthly_cost_under_ceiling
✔ Passed final evaluator
```

Exit code: `0`. To limit the sum to particular resource types instead, list them: `"resource_type": ["aws_instance", "aws_db_instance"]`.

## Tolerate a missing key

By default a value the provider cannot find fails the check. `error_tolerance` turns "the data is absent" into a **skip** instead — here the logging level is validated only when a `logging` block exists at all. Encryption, by contrast, gets no tolerance: its absence must fail.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json",
    "id": "encryption-and-optional-logging",
    "name": "Encryption required, logging checked when configured",
    "description": "Encryption must be enabled. The logging level is validated only when the logging block exists."
  },
  "evaluators": [
    {
      "id": "encryption_enabled",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "spec.encryption.enabled"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    },
    {
      "id": "logging_level_is_valid",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "spec.logging.level"
      },
      "condition": {
        "type": "ContainedIn",
        "value": ["INFO", "WARN", "ERROR"],
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "encryption_enabled && logging_level_is_valid"
}
```

```json
{
  "spec": {
    "encryption": {
      "enabled": true
    }
  }
}
```

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json
```

```text
Check: encryption_enabled
  PASSED
    1. PASSED: `true` is equal to `true`

Check: logging_level_is_valid
  SKIPPED
    1. SKIPPED: key_path: `spec.logging.level` is not found (severity: 2)

Passed: 1 Failed: 0 Skipped: 1

Final expression used:
-> encryption_enabled && logging_level_is_valid
✔ Passed final evaluator
```

Exit code: `0`. The skipped check is removed from `eval_expression` — the expression effectively becomes `encryption_enabled` — so the policy passes. The missing `key_path` is a severity-2 provider error; `"error_tolerance": 2` absorbs it. If the input *does* contain `spec.logging.level`, the value is validated normally and `DEBUG` would fail the policy.

One consequence to be aware of: if **every** check in the expression is skipped, the final verdict is neither pass nor fail. Running only the tolerant check against the same input:

```text
Check: logging_level_is_valid
  SKIPPED
    1. SKIPPED: key_path: `spec.logging.level` is not found (severity: 2)

Passed: 0 Failed: 0 Skipped: 1

Final expression used:
-> logging_level_is_valid
= Skipped final evaluator
```

Exit code: `1` — with `--fail-on-error`, an all-skipped run counts as an error, not a pass, because nothing was actually verified. Without the flag the exit code is `0`, like every other outcome.

## Parameterize the policy with variables

The same cost-ceiling policy, with the limit supplied at run time. A variable reference must be the entire string value; it is replaced with the variable's JSON value, so a number stays a number.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/infracost",
    "id": "parameterized-cost-ceiling",
    "name": "Monthly cost stays under a configurable ceiling",
    "description": "The estimated total monthly cost must not exceed the ceiling supplied as a variable."
  },
  "evaluators": [
    {
      "id": "cost_under_ceiling",
      "provider_args": {
        "operation_type": "total_monthly_cost",
        "resource_type": ["*"]
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": "{{ var.max_monthly_cost }}"
      }
    }
  ],
  "eval_expression": "cost_under_ceiling"
}
```

```json
{
  "max_monthly_cost": 300
}
```

Run against the same `input.json` as the previous cost recipe (total: 413.60):

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json -var-path variables.json
```

```text
Check: cost_under_ceiling
  FAILED
    1. FAILED: `413.6` is not less than or equal to `300`

Passed: 0 Failed: 1 Skipped: 0

Final expression used:
-> cost_under_ceiling
✘ Failed final evaluation
```

Exit code: `3`.

An inline `-var` overrides the variable file:

```bash
tirith --fail-on-error -policy-path policy.json -input-path input.json \
  -var-path variables.json -var 'max_monthly_cost=1000'
```

```text
Check: cost_under_ceiling
  PASSED
    1. PASSED: `413.6` is less than equal to `1000`

Passed: 1 Failed: 0 Skipped: 0

Final expression used:
-> cost_under_ceiling
✔ Passed final evaluator
```

Exit code: `0`. If a referenced variable is not supplied at all, the policy is not evaluated: the output reports `Variables not found: max_monthly_cost` and there is no verdict (exit `1` with `--fail-on-error`). The full substitution rules are in the [Policy Reference](./tirith-policy-reference.md#variables).
