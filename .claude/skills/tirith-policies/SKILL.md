---
name: tirith-policies
description: Write, validate, run and debug Tirith IaC governance policies, install Tirith, and add it to a CI pipeline. Use when writing or editing files under .tirith/policies, when a Tirith check fails in CI, when asked to add a guardrail to a Terraform or OpenTofu pipeline, or when reading a Tirith result document or exit code.
---

# Tirith

Tirith evaluates the plan a pipeline already produces against declarative JSON policies, and
exits non-zero so a violating change never reaches `apply`.

A policy is **JSON data, not a program**. It names a provider, the value to inspect, and the
condition that value must satisfy. Tirith does the traversal and returns resource-level evidence.

## The one rule

**Never hand back a policy you have not run.** A policy that matches nothing looks identical to
one that works — same shape, same silence, and it reports `final_result: null`, which is not a
pass. Lint it, then evaluate it against a document that *should* fail it.

```bash
tirith lint .tirith/policies
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

## Write a policy

Work in this order. Guessing any of the four is the main source of silently-broken policies.

1. **Which document are you reading?** An OpenTofu or Terraform plan, a Kubernetes manifest, an Infracost
   breakdown, or arbitrary JSON. That fixes `meta.required_provider`.
2. **Which operation?** Each provider exposes a closed set — see `reference/schema.md`.
3. **Which key names the value?** It differs per provider, and the wrong one is *ignored*
   rather than rejected, so the check reads nothing and passes. See `reference/schema.md`.
4. **Which condition?** 13 of them, listed in `reference/schema.md`. There is no `Exists`.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "name": "Every resource carries a costcenter tag"
  },
  "evaluators": [{
    "id": "costcenter_tag_present",
    "description": "Every taggable resource declares a costcenter tag",
    "provider_args": {
      "operation_type": "attribute",
      "terraform_resource_type": "*",
      "terraform_resource_attribute": "tags.costcenter"
    },
    "condition": {"type": "IsNotEmpty"}
  }],
  "eval_expression": "costcenter_tag_present"
}
```

`eval_expression` combines evaluator **ids** with `&&`, `||`, `!` and parentheses. An evaluator
the expression never names cannot affect the verdict. `!` is the only negation mechanism — there
are no inverse conditions, so write the positive detector and invert it.

## Before you hand it back

1. Does `eval_expression` reference every evaluator you wrote?
2. Is every `condition.type` in the closed list?
3. Did `tirith lint` pass?
4. Did you **run it** against a document that should fail it?

## Reference

| File | Use it for |
| --- | --- |
| `reference/schema.md` | The closed vocabulary: conditions, providers, operations, argument keys |
| `reference/validate.md` | `tirith lint`, and the traps it catches |
| `reference/verdicts.md` | Running a policy, exit codes, and finding the resource behind a failure |
| `reference/terraform-plan.md` | The plan provider's seven operations, for OpenTofu and Terraform |
| `reference/other-providers.md` | Kubernetes, Infracost and arbitrary JSON |
| `reference/variables.md` | One policy across environments with `-var` |
| `reference/install.md` | Installing Tirith |
| `reference/pipelines.md` | Adding Tirith to GitHub Actions, GitLab, or any container CI |
| `reference/platform.md` | Evaluating against an organization's central policies |
| `reference/debug-ci.md` | Starting from a red build and ending at the rule and the resource |

Worked policy/input pairs live in `src/tirith/tui/examples/` in the Tirith repository.
