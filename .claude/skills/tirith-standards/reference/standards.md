# The standards catalogue

One row per standard. Every `provider_args` block below is
`"required_provider": "stackguardian/terraform_plan"` unless it says otherwise, and every
`error_tolerance` goes **inside `condition`**.

**Every entry scoped to a resource type needs the guard evaluator from `SKILL.md`**, not just the
tolerance shown here. Without it the policy is red on any plan that does not touch that type:
exit `3` at tolerance `0`, exit `1` at tolerance `1`. The tolerance shown per standard is the one
to pair with the guard.

Read `../../tirith-policies/reference/schema.md` for the closed condition list. There is no
`Exists`, no `Matches`, no `In` and no `NotRegexMatch`.

---

## Tags

### Every resource carries a tag key

```json
{
  "operation_type": "attribute",
  "terraform_resource_type": "*",
  "terraform_resource_attribute": "tags.Owner"
}
```
`IsNotEmpty`, no `error_tolerance`.

`"*"` is right here: the rule is "everything", and a plan always contains something. Leaving the
tolerance at the default is what makes a missing tag fail, because an absent attribute is
severity `2`.

**Trap.** `"*"` includes resource types that cannot be tagged at all
(`aws_iam_role_policy_attachment`, `random_id`, `null_resource`, every data source). Those fail
on a rule they can never satisfy. If the repository has them, scope to the taggable types you
actually use, one policy per type or one evaluator per type combined with `&&`, and set
`error_tolerance: 1` on each.

**Trap.** AWS provider v4+ splits tags into `tags` and `tags_all`. `tags` holds what the
resource declares; `tags_all` includes provider-level `default_tags`. If your organization sets
`default_tags`, check `tags_all.Owner` or the rule fails on resources that inherit correctly.

### A tag must take one of a fixed set of values

```json
{
  "operation_type": "attribute",
  "terraform_resource_type": "aws_instance",
  "terraform_resource_attribute": "tags.Environment"
}
```
`ContainedIn` with `"value": ["dev", "staging", "prod"]`, `error_tolerance: 1`.

**Trap.** `ContainedIn` on two lists is element membership, not subset. If the attribute is
itself a list, this asks a different question than you think.

### A tag must match a shape

`RegexMatch` with `"value": "^[a-z]+-[0-9]{4}$"` on `tags.CostCentre`, `error_tolerance: 1`.

**Trap.** `RegexMatch` against `null` does not match, so an absent tag fails. That is usually
what you want; say so in `meta.description` so nobody later "fixes" it with a tolerance.

---

## Naming conventions

The attribute holding the name **differs per resource type**. There is no generic `name`.

| Type | Attribute |
| --- | --- |
| `aws_s3_bucket` | `bucket` |
| `aws_instance` | `tags.Name` |
| `aws_db_instance` | `identifier` |
| `aws_iam_role`, `aws_lambda_function`, `aws_ecs_cluster` | `name` / `function_name` |
| `azurerm_*` | `name` |
| `google_*` | `name` |

```json
{
  "operation_type": "attribute",
  "terraform_resource_type": "aws_s3_bucket",
  "terraform_resource_attribute": "bucket"
}
```
`RegexMatch` with `"value": "^acme-(dev|staging|prod)-[a-z0-9-]+$"`, `error_tolerance: 1`.

**Trap, and it is the big one.** A name the plan does not know yet arrives as `null`. That
happens with `bucket_prefix`, with `name_prefix`, and with any name built from an attribute of a
resource being created in the same plan. `RegexMatch` against `null` fails, so the rule rejects
a change that is actually fine. Check the repository for `_prefix` arguments before shipping a
naming rule, and if they are in use, scope the rule to the resources that set a literal name.

**Trap.** Anchor the pattern. `"acme-"` without `^` matches `not-acme-prod-thing`.

---

## Allowed regions

Region is not a resource attribute; it lives on the provider block.

```json
{
  "operation_type": "provider_config",
  "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
  "attribute_to_get": "region"
}
```
`ContainedIn` with `"value": ["eu-central-1", "eu-west-1"]`.

**Trap.** The full registry name is required, not `aws`. A wrong name is severity `1`.

**Trap.** A region supplied by an environment variable or by an aliased provider will not appear
here. This rule proves the declared region, not the effective one.

---

## Permitted and forbidden resource types

Forbid a type by counting it:

```json
{"operation_type": "count", "terraform_resource_type": "aws_iam_user"}
```
`Equals` with `"value": 0`.

**Trap.** `count` measures the root module and includes no-op resources, so a resource that is
merely present and unchanged still counts. This rule reads "must not exist in this
configuration", not "must not be created by this change".

---

## Size ceilings

```json
{
  "operation_type": "attribute",
  "terraform_resource_type": "aws_ebs_volume",
  "terraform_resource_attribute": "size"
}
```
`LessThanEqualTo` with `"value": 100`, `error_tolerance: 1`.

For instance types, prefer `ContainedIn` against an allow-list over a regex: an allow-list is
readable in a diff and a regex over instance families is not.

---

## Encryption and public access

```json
{
  "operation_type": "attribute",
  "terraform_resource_type": "aws_ebs_volume",
  "terraform_resource_attribute": "encrypted"
}
```
`Equals` with `"value": true`, `error_tolerance: 1`.

**Trap.** `true` and `"true"` are different questions. `condition.value` keeps its JSON type.

**Trap.** An argument the configuration omits is often present in the plan as the schema default,
so it is checkable. An argument that is genuinely absent is severity `2` and fails at tolerance
`1`, which for an encryption rule is the correct outcome: unset encryption is unencrypted.

---

## Provider version pinning

```json
{
  "operation_type": "terraform_version"
}
```
`GreaterThanEqualTo` with `"value": "1.6.0"`.

**Trap.** This is a string comparison. `"1.10.0"` sorts below `"1.6.0"`. Pin a floor you are
confident about lexically, or state the limitation in `meta.description`.

---

## Module source restrictions

There is no operation that reads a module's `source`. The nearest available check is
`direct_references`, which reports what a resource references, and it produces no edge for
`var`, `local` or `module` references.

**Say so rather than approximating.** "Only modules from our registry" is not expressible today.
Tracking: the roadmap's `module_address` filter would make it so.

---

## Assembling the set

- One file per standard under `.tirith/policies/`, named for the rule.
- Fill `meta.name` and `meta.description`. The description is where a trap gets recorded, and it
  is what a person reads when the check fires eighteen months from now.
- `meta.severity` and `meta.tags` are carried into the result document but nothing gates on them
  yet, so do not build a workflow that depends on them.
- Run `tirith lint .tirith/policies` before running anything against a plan.
- Prove each policy against a document that should fail it.
