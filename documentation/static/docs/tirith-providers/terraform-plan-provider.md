# Terraform Plan Provider

Source: https://stackguardian.github.io/tirith/docs/tirith-providers/terraform-plan-provider/
Summary: Reference for the stackguardian/terraform_plan provider - operation types, parameters, return shapes, and error behavior.

```
required_provider: stackguardian/terraform_plan
```

Inspects a Terraform plan: attribute values of changed resources, the actions applied to them, resource counts, explicit dependencies, references between resources, provider configuration, and the Terraform version.

## Input document

The JSON representation of a Terraform plan:

```bash
terraform plan -out=plan.out
terraform show -json plan.out > plan.json
tirith -policy-path policy.json -input-path plan.json
```

Most operations read the `resource_changes` array of the plan. If the plan contains no `resource_changes` at all, every operation reports an error with severity 0 (`No Terraform resources changes are found`), which is skipped at the default `error_tolerance` of 0.

## Operation types

| `operation_type` | Purpose |
|---|---|
| `attribute` | Get an attribute's planned value for every instance of a resource type |
| `action` | Get the plan actions (`create`, `update`, `delete`, ...) for a resource type |
| `count` | Count the changed instances of a resource type |
| `direct_dependencies` | Get the resource types listed in a resource's `depends_on` |
| `direct_references` | Get or check references between resources |
| `terraform_version` | Get the Terraform version that produced the plan |
| `provider_config` | Get the configuration of a Terraform provider (version constraint or region) |

Any other `operation_type` produces an error with severity 99, which fails the check.

---

## `attribute`

Returns the planned (`change.after`) value of an attribute for every instance of a resource type.

| Parameter | Required | Description |
|---|---|---|
| `terraform_resource_type` | yes | Resource type to match (e.g. `aws_s3_bucket`), or `*` to match every type. |
| `terraform_resource_attribute` | yes | Attribute to read. A plain top-level key (`force_destroy`), a dotted path (`tags.costcenter`), or a path containing `.*.` to iterate over a list (`ebs_block_device.*.encrypted`). |
| `exclude_resource_types` | no (default `[]`) | List of resource types to skip. Only applied when `terraform_resource_type` is `*`. |

**Returns:** one value per matching resource instance. With a `.*.` wildcard, one value per list element; list elements that lack the attribute contribute `null`, so they are still evaluated. The value is whatever the attribute holds in the plan — scalar, list, or dict.

**On a miss:**

- No resource of the requested type in `resource_changes` — severity 1 (`resource_type: '...' is not found`).
- Resource found, attribute absent — severity 2 (`attribute: '...' is not found`), reported per resource instance that lacks it.
- Resource found but its `change.after` is empty (e.g. a destroy-only change) — severity 0 (`No Terraform changes found for resource type: '...'`).

Example (adapted from a test fixture; requires every resource in the plan to carry a non-empty `costcenter` tag):

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "every_resource_has_costcenter_tag",
      "description": "All resources must have a 'costcenter' tag with a non-empty value",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "*",
        "terraform_resource_attribute": "tags.costcenter",
        "exclude_resource_types": ["aws_iam_role_policy_attachment"]
      },
      "condition": {
        "type": "IsNotEmpty",
        "value": "",
        "error_tolerance": 1
      }
    }
  ],
  "eval_expression": "every_resource_has_costcenter_tag"
}
```

---

## `action`

Returns the actions Terraform plans to take on every instance of a resource type. Actions come straight from `change.actions` in the plan: `create`, `update`, `delete`, `no-op`, `read` (a replacement appears as both `delete` and `create`).

| Parameter | Required | Description |
|---|---|---|
| `terraform_resource_type` | yes | Resource type to match, or `*` for every type. |
| `exclude_resource_types` | no (default `[]`) | List of resource types to skip. Only applied when `terraform_resource_type` is `*`. |

**Returns:** one string per action per matching resource instance (a resource with actions `["delete", "create"]` yields two values).

**On a miss:** no resource of the requested type — severity 1.

Example (adapted from a test fixture; fails when a virtual network would be deleted):

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "vnet_is_deleted",
      "provider_args": {
        "operation_type": "action",
        "terraform_resource_type": "azurerm_virtual_network"
      },
      "condition": {
        "type": "ContainedIn",
        "value": ["delete"],
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "!vnet_is_deleted"
}
```

---

## `count`

Counts the instances of a resource type in `resource_changes`.

| Parameter | Required | Description |
|---|---|---|
| `terraform_resource_type` | yes | Resource type to count, or `*` for every type. |
| `exclude_resource_types` | no (default `[]`) | List of resource types to skip. Only applied when `terraform_resource_type` is `*`. |

**Returns:** a single integer. A type with no instances returns `0` — this operation never produces a "not found" error.

Example:

```json
{
  "id": "at_most_ten_vpcs",
  "provider_args": {
    "operation_type": "count",
    "terraform_resource_type": "aws_vpc"
  },
  "condition": {
    "type": "LessThanEqualTo",
    "value": 10
  }
}
```

---

## `direct_dependencies`

Returns, for each resource of a type, the resource types named in its explicit `depends_on`. Only resources declared in the **root module** of the configuration are inspected.

| Parameter | Required | Description |
|---|---|---|
| `terraform_resource_type` | yes | Resource type to inspect. Omitting it produces a severity 99 error. |

**Returns:** one list of resource-type strings per matching resource (only the type part of each `depends_on` entry, i.e. `aws_s3_bucket.example` becomes `aws_s3_bucket`). A resource without `depends_on` yields an empty list.

**On a miss:** no resource of the requested type in the configuration — severity 1.

Example (verified against a test fixture; requires every EC2 instance to declare an explicit dependency on an S3 bucket):

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [
    {
      "id": "ec2_depends_on_s3",
      "description": "Make sure that EC2 instances have explicit dependency on S3 bucket",
      "provider_args": {
        "operation_type": "direct_dependencies",
        "terraform_resource_type": "aws_instance"
      },
      "condition": {
        "type": "Contains",
        "value": "aws_s3_bucket",
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "ec2_depends_on_s3"
}
```

---

## `direct_references`

Inspects references between resources (a reference is created when one resource's argument uses another resource's attribute, e.g. `security_groups = [aws_security_group.sg.id]`). It has three modes, chosen by which parameters are present:

| Parameter | Required | Description |
|---|---|---|
| `terraform_resource_type` | yes | The resource type under inspection. |
| `referenced_by` | no | A resource type that should point **at** `terraform_resource_type`. |
| `references_to` | no | A resource type that `terraform_resource_type` should point **to**. |

`referenced_by` and `references_to` are mutually exclusive — supplying both produces a severity 99 error.

### Plain mode (neither `referenced_by` nor `references_to`)

For each resource of `terraform_resource_type` declared in the **root module**, returns the list of resource types it references in its expressions.

**Returns:** one list of resource-type strings per matching resource.

**On a miss:** type not found in the configuration — severity 1. Omitting `terraform_resource_type` — severity 99.

Example (verified against a test fixture):

```json
{
  "id": "aws_elbs_have_direct_references_to_security_group",
  "provider_args": {
    "operation_type": "direct_references",
    "terraform_resource_type": "aws_elb"
  },
  "condition": {
    "type": "Contains",
    "value": "aws_security_group",
    "error_tolerance": 2
  }
}
```

### `referenced_by` mode

Checks that instances of `terraform_resource_type` are referenced by resources of type `referenced_by`. Instances that are only being destroyed are ignored. Unlike the plain mode, references are searched through the whole configuration, including child modules.

**Returns:** one boolean per instance of `terraform_resource_type` — `true` if some `referenced_by` resource references it, `false` otherwise. Use `"condition": {"type": "Equals", "value": true}` to require that all instances are referenced.

**On a miss:** no (non-destroyed) instance of `terraform_resource_type` — severity 1.

Example (from a test fixture; every S3 bucket must have an intelligent-tiering configuration attached):

```json
{
  "meta": {
    "required_provider": "stackguardian/terraform_plan",
    "version": "v1"
  },
  "evaluators": [
    {
      "id": "s3HasLifeCycleIntelligentTiering",
      "description": "Make sure all aws_s3_bucket are referenced by aws_s3_bucket_intelligent_tiering_configuration",
      "provider_args": {
        "operation_type": "direct_references",
        "terraform_resource_type": "aws_s3_bucket",
        "referenced_by": "aws_s3_bucket_intelligent_tiering_configuration"
      },
      "condition": {
        "type": "Equals",
        "value": true,
        "error_tolerance": 0
      }
    }
  ],
  "eval_expression": "s3HasLifeCycleIntelligentTiering"
}
```

### `references_to` mode

Checks that every instance of `terraform_resource_type` references at least one resource of type `references_to`. Instances that are only being destroyed are ignored.

**Returns:** a **single** boolean — `true` only if all instances reference the target type.

**On a miss:** no (non-destroyed) instance of `terraform_resource_type` — severity 1.

Example (verified against a test fixture):

```json
{
  "id": "elbRefsToSecGroup",
  "description": "Make sure ELBs references to security groups",
  "provider_args": {
    "operation_type": "direct_references",
    "terraform_resource_type": "aws_elb",
    "references_to": "aws_security_group"
  },
  "condition": {
    "type": "Equals",
    "value": true,
    "error_tolerance": 0
  }
}
```

---

## `terraform_version`

Returns the Terraform version string recorded in the plan.

No parameters besides `operation_type`.

**Returns:** a single string (e.g. `"1.4.5"`), or `null` if the plan has no `terraform_version` key.

Example (verified end-to-end):

```json
{
  "id": "terraform_version_check",
  "provider_args": {
    "operation_type": "terraform_version"
  },
  "condition": {
    "type": "RegexMatch",
    "value": "^1\\."
  }
}
```

---

## `provider_config`

Reads the configuration of a Terraform provider from `configuration.provider_config` in the plan.

| Parameter | Required | Description |
|---|---|---|
| `terraform_provider_full_name` | yes | The provider's full registry name, e.g. `registry.terraform.io/hashicorp/aws`. Omitting it produces a severity 99 error. |
| `attribute` | yes | What to read. Must be `version_constraint` or `region` — anything else produces a severity 99 error. |

**Returns:** one string per provider entry whose `full_name` matches: the version constraint (e.g. `">= 3.11.0, < 4.0.0"`) or the region. The region is only found when it is written as a constant in the configuration; a region supplied through a variable is reported as not found (severity 2).

**On a miss:**

- Matching provider found but the attribute is absent — severity 2 (`` `region` is not found in the provider_config ``).
- No provider with that `full_name` — severity 1.

Example (verified end-to-end):

```json
{
  "id": "aws_region_check",
  "provider_args": {
    "operation_type": "provider_config",
    "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
    "attribute": "region"
  },
  "condition": {
    "type": "ContainedIn",
    "value": ["eu-central-1", "eu-west-1"]
  }
}
```

---

## Error severities used by this provider

| Severity | Situation |
|---|---|
| 0 | No `resource_changes` in the plan, or the matched resource has no planned values (destroy-only change). |
| 1 | Resource type / provider name not found. |
| 2 | Attribute not found on a matched resource or provider config. |
| 99 | Invalid `provider_args` (unsupported operation or attribute, missing required parameter, both `referenced_by` and `references_to` given). |

Whether a severity fails or skips the check depends on `condition.error_tolerance` — see the [providers overview](overview.md) and [error tolerance](../tirith-policies/tirith-policy-error-tolerance.md). Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md).
