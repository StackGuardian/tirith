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
nothing about a destroy is visible through it. Use `action`.

## `action` emits one result per action

A resource's `change.actions` is a list: `["create"]`, `["update"]`, `["delete"]`, or for a
replacement `["delete", "create"]` / `["create", "delete"]`. The `action` operation emits **one
result per element**, and the evaluator fails if any element fails. Two forms follow from that,
and they mean different things:

**Block every delete, including a replacement.** The universal form: every action must be
something other than `delete`. No negation.

```json
{
  "id": "no_database_delete",
  "provider_args": {"operation_type": "action", "terraform_resource_type": "aws_db_instance"},
  "condition": {"type": "NotEquals", "value": "delete"}
}
```

with `"eval_expression": "no_database_delete"`. Exit `3` on `["delete"]` and on
`["delete", "create"]`; exit `0` on `["update"]`.

**Block only a pure delete, allow a replacement.** The detector form: `ContainedIn ["delete"]`
passes on a `delete` element and fails on any other, so on a replacement the evaluator has one
pass and one fail, fails as a whole, and `!` turns that into a pass.

```json
{"condition": {"type": "ContainedIn", "value": ["delete"]}}
```

with `"eval_expression": "!no_database_delete"`. Exit `3` only on `["delete"]`.

Two traps, both verified against the engine:

- The action is spelled `delete`, never `destroy`. `"value": ["destroy"]` matches nothing and the
  policy exits `0` on a real delete.
- The order of `["delete", "create"]` versus `["create", "delete"]` cannot be tested. Each element
  is evaluated on its own.

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
  A skipped resource does not touch the verdict of the others: the evaluator still fails if any
  resource fails, and is skipped as a whole only when every resource was tolerated away.

On a wildcard policy every message reads identically, and only the resource address in the result
distinguishes one finding from another.
