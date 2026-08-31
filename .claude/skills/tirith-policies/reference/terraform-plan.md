# The plan provider — OpenTofu and Terraform

`"required_provider": "stackguardian/terraform_plan"` reads the output of
`tofu show -json tfplan` or `terraform show -json tfplan`. The provider is named for
Terraform because it predates the fork, but it reads either tool's plan: both emit the same
`resource_changes` structure, and nothing in the provider inspects which binary produced it.

**There is no `stackguardian/terraform_state` provider.** The registry holds five providers and
that is not one of them. To write a policy about a state file, read it with
`stackguardian/json` and `key_path` — a state document is ordinary JSON. (`tirith platform check
--input-kind terraform_state` is a different thing: it tells the uploader to mask the document as
state before it leaves your machine, and the evaluation still runs through the json provider.)

Arguments: `terraform_resource_type` selects the resources (`"*"` = every type), and
`terraform_resource_attribute` names the value. Dot-separated, `*` wildcards a list.

## The seven operations

| `operation_type` | Returns | Use it for |
| --- | --- | --- |
| `attribute` | The value at `terraform_resource_attribute` | Most policies: tags, encryption flags, sizes |
| `action` | The planned actions for each resource | Blocking destroys and replacements |
| `count` | How many resources of the type exist | Ceilings on resource counts |
| `direct_references` | Whether resources reference a given type | "Every ELB has a security group" |
| `direct_dependencies` | The resource's declared dependencies | Ordering and coupling rules |
| `provider_config` | Provider-level configuration | Pinning a region or a provider setting |
| `terraform_version` | The version recorded in the plan | Requiring a minimum OpenTofu or Terraform version |

## `attribute` cannot see a destroy

`attribute` reads **`change.after` only**. A resource being destroyed has `after: null`, so
nothing about a destroy is visible through it. Use `action`:

```json
{
  "id": "no_database_destroy",
  "provider_args": {
    "operation_type": "action",
    "terraform_resource_type": "aws_db_instance"
  },
  "condition": {"type": "ContainedIn", "value": ["destroy"]}
}
```

with `"eval_expression": "!no_database_destroy"` — the check *detects* a destroy, and `!` turns
detection into refusal.

## Replacement is two actions, not one

A replacement appears as `["delete", "create"]` or `["create", "delete"]`, and the order matters:
destroy-first means downtime, create-first does not. If the distinction matters to your rule, test
the ordering rather than the presence of `delete`.

## `count` measures the module, not the change

`count` has no action filter, and both tools report unchanged resources as `no-op`. So `count` with
`terraform_resource_type: "*"` measures **root-module size**, not the size of the change. Blast
radius is not expressible today — do not write a policy that claims to cap it.

## `direct_references`

Answers "is every X referenced by a Y", which attribute checks cannot express:

```json
{
  "id": "elb_has_security_group",
  "provider_args": {
    "operation_type": "direct_references",
    "terraform_resource_type": "aws_elb",
    "references_to": "aws_security_group"
  },
  "condition": {"type": "Equals", "value": true, "error_tolerance": 0}
}
```

`referenced_by` inverts the direction — "every bucket is referenced by a tiering configuration".

## Wildcards and missing attributes

`terraform_resource_type: "*"` with a specific attribute will hit resources that do not have that
attribute at all. Those raise severity `2`. Decide deliberately:

- `error_tolerance: 0` — a resource without the attribute **fails**. Right for "everything must be
  tagged".
- `error_tolerance: 2` — it is **skipped**. Right for "where this attribute exists, it must be X".

On a wildcard policy every message reads identically, and only the resource address in the result
distinguishes one finding from another.
