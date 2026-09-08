---
name: tirith-standards
description: Generate a Tirith policy set for an existing Terraform or OpenTofu repository, covering organization standards such as required tags, naming conventions, allowed regions, permitted resource types, sizes and encryption defaults. Use when asked to add guardrails to a repository that has no policies yet, to enforce a tagging or naming standard, to codify a team convention, or to produce a starting policy set from existing IaC. Requires the tirith-policies skill for the vocabulary.
---

# Standards policies from existing IaC

A catalogue of generic checks is not what stops your incidents. The rules that do are the ones
only your organization can state: the tag your finance team reconciles against, the module
registry you are allowed to pull from, the two regions your data residency answer depends on.

This skill turns a repository you already have into that policy set.

## Vocabulary comes from `tirith-policies`

Do not write policy JSON from memory. Read `../tirith-policies/reference/schema.md` for the
closed list of providers, operations, argument keys and the thirteen condition types. If that
skill is not installed, fetch `https://stackguardian.github.io/tirith/llms.txt` and follow it to
the schema page. Everything below assumes that vocabulary.

## The boundary that decides every policy: HCL in, plan out

You read `.tf` and `.tofu` files to **discover** what to write policies about. The policies
themselves never see that HCL. They evaluate `terraform show -json` output, where:

| In your code | In the plan |
| --- | --- |
| `var.environment`, `local.tags`, `${}` interpolation | already resolved to a value, or `null` when it is not known until apply |
| a `module` block | its resources, at addresses like `module.vpc.aws_subnet.this[0]` |
| `count` / `for_each` | one resource instance per element |
| a computed name | `null`, because the plan does not know it yet |
| `dynamic` blocks | the blocks they expanded into |

So: never write a policy about a variable, a local, or a module block. Write it about the
resource attribute the plan will carry. A standard that is only enforceable in HCL (for example
"always use our module rather than the raw resource") is expressible as
`direct_references` or as a `provider_config` check, or not at all. Say which, rather than
producing a policy that reads nothing.

## The rule that catches most generated policies

```
severity > error_tolerance  ->  the check FAILS
otherwise                   ->  the check is SKIPPED
```

`DEFAULT_ERROR_TOLERANCE` is `0`, and the plan provider raises severity `1` when the resource
type is absent from the plan and `2` when the attribute is absent from the resource.

**Therefore a policy scoped to one resource type has no green outcome on a plan that does not
touch that type.** Both tolerance settings are red, in different ways, and this is the single
most common defect in a generated standards set:

| `error_tolerance` | Plan has no resource of that type | Reads as |
| --- | --- | --- |
| omitted, so `0` | `1 > 0`, the check **fails**, exit `3` | your infrastructure violates a policy |
| `1` | the check is **skipped**, so every check is skipped, `final_result: null`, exit `1` | Tirith could not reach a verdict |

### Guard every type-scoped policy

`count` behaves differently from `attribute` on an absent type: it returns `0` rather than
raising severity `1`. So it can gate the rule.

```json
{
  "evaluators": [
    {"id": "not_applicable",
     "provider_args": {"operation_type": "count", "terraform_resource_type": "aws_s3_bucket"},
     "condition": {"type": "Equals", "value": 0}},
    {"id": "the_rule", "provider_args": {"...": "..."},
     "condition": {"type": "RegexMatch", "value": "...", "error_tolerance": 1}}
  ],
  "eval_expression": "not_applicable || the_rule"
}
```

Verified on the engine: exit `3` when a bucket breaks the rule, `0` when they all satisfy it,
`0` when the plan touches no bucket at all. `examples/org-standards/` is that policy with its
three plans.

Keep `error_tolerance: 1` on the rule alongside the guard, so the not-applicable case is
*skipped* rather than *failed and then masked by the `||`*. Both give exit `0`; only one leaves
a clean result document.

| Standard | Scope | Shape |
| --- | --- | --- |
| Presence, all types | `"*"` | no guard needed, omit the tolerance. A plan always contains something |
| Anything scoped to a type | `aws_s3_bucket` | guard + `error_tolerance: 1` |
| Anything | any | never `2`. It forgives the missing attribute, which is the thing you were checking |

Deletes are safe by default: a destroyed resource is severity `0`, which the default tolerance
skips rather than fails.

## Protocol

1. **Inventory the repository.** List every distinct `resource "TYPE" "NAME"` across `.tf` and
   `.tofu` files. Group by provider (`aws_`, `azurerm_`, `google_`). Note which types are used
   more than once: those are where a standard pays for itself. Note the modules in use and where
   they are sourced from.

2. **Extract the conventions already there.** Read the existing code before proposing rules. What
   tag keys appear on most resources? What naming pattern do the existing names follow? Which
   regions and instance sizes appear? A standard the repository already follows is a rule you can
   enforce today without a migration; a standard it does not follow yet is a change request, and
   you must say so rather than shipping a policy that fails on day one.

3. **Propose before writing.** Give the user a table: standard, the resource types it would cover,
   how many resources in the repository would pass today, and how many would fail. Let them
   choose. Do not generate thirty policies unasked.

4. **Write one file per standard**, under `.tirith/policies/`, named for the rule
   (`required-tags.json`, `naming-s3.json`). One concern per file: a single policy combining tags
   and naming reports one verdict for two unrelated problems, and the person who has to fix it
   cannot tell which fired.

5. **Prove each one.** For every policy, produce a plan document that violates it and confirm
   `tirith -policy-path P -input-path should-fail.json --fail-on-error` exits `3`, then one that
   satisfies it and confirm exit `0`. A policy that has only been seen passing is untested. Run
   `tirith lint` over the directory first: it catches an invented condition type or a misplaced
   `error_tolerance` without needing any plan at all.

6. **Report what you could not express.** Name the standard, name what Tirith would need, and stop.
   A policy that approximates a rule without saying so is worse than an absent one.

## The standards catalogue

`reference/standards.md` carries one row per standard: the exact `provider_args`, the condition,
the tolerance, and the trap specific to that standard. Read it before writing any of them. It
covers required tags, tag value shape, naming conventions, allowed regions, permitted and
forbidden resource types, size ceilings, encryption and public-access defaults, provider version
pinning, and module source restrictions.

## What not to generate

| | Why |
| --- | --- |
| A policy per resource instance | Standards are about types, not addresses. `terraform_resource_type` already quantifies over every instance |
| A policy about `var.` or `local.` | Neither survives into the plan. See the boundary table above |
| `error_tolerance: 2` on a presence check | It forgives exactly the case the check exists to catch |
| A rule the repository does not already follow, shipped silently | It fails on the first run and gets disabled. Propose it as a change first |
| Thirty policies from one request | Propose the set, ship what is agreed |

## Worked example

`examples/org-standards/` holds a naming policy with the plan that violates it and the plan that
satisfies it, including the `error_tolerance: 1` that keeps it quiet on unrelated changes.
