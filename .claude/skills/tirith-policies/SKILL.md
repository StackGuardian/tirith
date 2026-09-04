---
name: tirith-policies
description: Write, validate, run and debug Tirith IaC governance policies, install Tirith, and add it to a CI pipeline (GitHub Actions, GitLab CI, Bitbucket Pipelines, Jenkins, Azure DevOps, CircleCI or any container runner). Use when writing or editing files under .tirith/policies, when a Tirith check fails in CI, when asked to add a guardrail to a Terraform or OpenTofu pipeline, or when reading a Tirith result document or exit code.
---

# Tirith

Tirith evaluates the plan a pipeline already produces against declarative JSON policies and exits
non-zero so a violating change never reaches `apply`. A policy is **JSON data, not a program**: it
names a provider, the value to inspect, and the condition that value must satisfy.

## Install

Not from PyPI. `pip install tirith` installs an **unrelated project**; `py-tirith` is the
`setup.py` name and is not published. Install from git, pinned to a tag:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
```

## The one rule

**Never hand back a policy you have not run against a document that should fail it.**

A policy that matches nothing looks identical to one that works. Run it against input you expect
to be refused. Exit `0` means it matched nothing and gates nothing.

```bash
tirith -policy-path .tirith/policies -input-path should-fail.json --fail-on-error; echo $?   # want 3
```

## Exit codes

| Exit | Meaning | What CI should do |
| --- | --- | --- |
| `0` | Every check passed | Continue to `apply` |
| `3` | A policy failed | Fail the job: the change was refused |
| `1` | No verdict could be reached | Fail the job, but report a **tool or input** problem |

- Never collapse `3` into `1`. A job that cannot tell them apart reports an outage as a violation.
- `2` is argparse's usage error, not a Tirith verdict. There is no timeout code; a platform
  timeout exits `1`.
- **`final_result: null` is not a pass.** Every check was skipped, nothing was evaluated, exit `1`.
- Without `--fail-on-error` the exit is always `0`. Every real gate needs the flag.

## Write a policy

Decide these four in order. Guessing any of them is the main source of silently broken policies.

1. **Document.** Terraform or OpenTofu plan, Kubernetes manifest, Infracost breakdown, or arbitrary
   JSON or YAML. This fixes `meta.required_provider`. Five providers ship; there is **no
   CloudFormation provider**, a template is arbitrary JSON read by `stackguardian/json`.
2. **Operation.** Each provider exposes a closed set: `reference/schema.md`.
3. **Key naming the value.** It differs per provider, and a wrong key is *ignored, not rejected*,
   so the check reads nothing and passes: `reference/schema.md`.
4. **Condition.** Thirteen, listed in `reference/schema.md`. There is no `Exists`.

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
it never names cannot affect the verdict. `!` is the only negation: write the positive detector
and invert it.

## Traps

- **`error_tolerance` goes inside `condition`.** On the evaluator it is silently ignored.
  `{"condition": {"type": "IsNotEmpty", "error_tolerance": 2}}`
- **One evaluator, one result per matching resource.** Three buckets give three results from one
  rule, and the check fails if any of them fails.
- **Missing attribute is severity 2, missing resource type is severity 1.** With
  `error_tolerance: 2` a resource lacking the attribute is *skipped*, not failed. If every
  evaluator is skipped the policy is `final_result: null`, exit `1`. Skipping is not passing.
- **A skipped resource can erase a failure (issue #293).** In one evaluator, a resource skipped by
  `error_tolerance` after a violating one resets the verdict to `null`, exit `1`. Destroys do this
  at every tolerance. Prefer one evaluator per resource type over a wildcard with tolerance.
- **A type-scoped policy refuses a plan with none of that type.** Severity 1 under the default
  tolerance is exit `3`; with `error_tolerance: 1` it is exit `1`. Neither is `0`. See
  `reference/verdicts.md`.
- **The delete action is spelled `delete`.** `"destroy"` matches nothing and the guard exits `0`.
  `action` emits one result per action: `NotEquals "delete"` blocks deletes and replacements,
  `ContainedIn ["delete"]` with `!` blocks only a pure delete. See `reference/terraform-plan.md`.
- **An unknown `condition.type` fails with no error attached.** It exits `3` and reads like a
  real violation. Check the type against the closed list, not your memory.
- **`tirith lint` does not ship.** Do not put it in a pipeline. `reference/validate.md` has
  what to do instead.

## Test it with the bundled example

`examples/required-tags/` holds the policy above, a plan that violates it and one that satisfies
it. Copy the pair and edit it when testing a new policy.

```bash
cd examples/required-tags
tirith -policy-path policy.json -input-path should-fail.json --fail-on-error; echo $?   # 3
tirith -policy-path policy.json -input-path should-pass.json --fail-on-error; echo $?   # 0
```

## Before you hand it back

1. Does `eval_expression` reference every evaluator you wrote?
2. Is every `condition.type` in the closed list of thirteen?
3. Is the argument key the one this provider reads?
4. Is `error_tolerance`, if used, inside `condition`?
5. Did you **run it** against a document that should fail it, and did it exit `3`?
6. Did you run it against a document that should pass, and did it exit `0`?

## Reference

| File | Use it for |
| --- | --- |
| `reference/schema.md` | The closed vocabulary: conditions, providers, operations, argument keys |
| `reference/validate.md` | Checking a policy is well-formed, and why `tirith lint` is not the way |
| `reference/verdicts.md` | Running a policy, exit codes, and finding the resource behind a failure |
| `reference/terraform-plan.md` | The plan provider's operations, for OpenTofu and Terraform |
| `reference/other-providers.md` | Kubernetes, Infracost and arbitrary JSON or YAML |
| `reference/variables.md` | One policy across environments with `-var` |
| `reference/install.md` | Installing Tirith, and why the install is a git URL |
| `reference/pipelines.md` | GitHub Actions, GitLab CI, Bitbucket, Jenkins, Azure DevOps, CircleCI |
| `reference/platform.md` | Evaluating against an organization's central policies |
| `reference/debug-ci.md` | Starting from a red build and ending at the rule and the resource |
| `examples/required-tags/` | A policy, a plan that fails it, and a plan that passes it |

Translating existing Sentinel policies is a separate skill, `tirith-migrate`, installed alongside
this one.
