---
name: tirith-policies
description: Write, validate, run and debug Tirith IaC governance policies, install Tirith, and add it to a CI pipeline (GitHub Actions, GitLab CI, Bitbucket Pipelines, Jenkins, Azure DevOps, CircleCI or any container runner). Use when writing or editing files under .tirith/policies, when a Tirith check fails in CI, when asked to add a guardrail to a Terraform or OpenTofu pipeline, or when reading a Tirith result document or exit code.
---

# Tirith

Tirith evaluates the plan a pipeline already produces against declarative JSON policies, and
exits non-zero so a violating change never reaches `apply`.

A policy is **JSON data, not a program**. It names a provider, the value to inspect, and the
condition that value must satisfy. Tirith does the traversal and returns resource-level evidence.

## Install: not from PyPI

`pip install tirith` installs an **unrelated project of the same name**. `pip install py-tirith`
finds nothing: that is the package name in `setup.py`, and it is not published. Install from git,
pinned to a tag:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
```

## The one rule

**Never hand back a policy you have not run against a document that should fail it.**

A policy that matches nothing looks identical to one that works: same shape, same silence. Run it
against input you expect to be refused. If that run exits `0`, the policy matched nothing and
gates nothing.

```bash
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

## Exit codes are a contract

| Exit | Meaning | What CI should do |
| --- | --- | --- |
| `0` | Every check passed | Continue to `apply` |
| `3` | A policy failed | Fail the job: the change was refused |
| `1` | No verdict could be reached | Fail the job, but report a **tool or input** problem |

`ExitStatus.ERROR_TIMEOUT = 2` is declared in `status.py` and returned nowhere, including on the
platform path, which maps a timeout to `1`. Do not branch a pipeline on it.

`3` is deliberately not `1`. Collapsing them reports an outage as a policy violation, and a job
that cannot tell them apart cannot tell a working gate from a broken one.

**`final_result: null` is not a pass.** It means every check was skipped, so the policy evaluated
nothing. It exits `1`.

## Write a policy

Work in this order. Guessing any of the four is the main source of silently-broken policies.

1. **Which document are you reading?** An OpenTofu or Terraform plan, a Kubernetes manifest, an
   Infracost breakdown, or arbitrary JSON or YAML. That fixes `meta.required_provider`. There are
   five providers and **no CloudFormation provider**: a CloudFormation template is arbitrary JSON,
   read by `stackguardian/json`.
2. **Which operation?** Each provider exposes a closed set: see `reference/schema.md`.
3. **Which key names the value?** It differs per provider, and the wrong one is *ignored* rather
   than rejected, so the check reads nothing and passes. See `reference/schema.md`.
4. **Which condition?** Thirteen, listed in `reference/schema.md`. There is no `Exists`.

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
the expression never names cannot affect the verdict. `!` is the only negation mechanism: there
are no inverse conditions, so write the positive detector and invert it.

## Four traps that cost the most time

**`error_tolerance` goes inside `condition`, not on the evaluator.** On the evaluator it is
silently ignored: no warning, and the check still fails.

```json
{"condition": {"type": "IsNotEmpty", "error_tolerance": 2}}
```

**One evaluator produces one result per matching resource.** A plan with three buckets gives three
results from one rule, and the check fails if any of them fails. That is the mechanism, not a
wildcard trick.

**A missing attribute is severity 2, a missing resource type is severity 1.** With
`error_tolerance: 2` a resource lacking the attribute is *skipped* rather than failed, which can
turn the whole policy into `final_result: null`. Skipping is not passing.

**`tirith lint` is not in the released package.** It is in development. The released CLI dispatches
`tirith`, `tirith ui` and `tirith platform check` and nothing else, so do not put it in a pipeline
you are writing for someone. Check policy shape by reading `reference/schema.md` and by running
the policy. See `reference/validate.md`.

## Before you hand it back

1. Does `eval_expression` reference every evaluator you wrote?
2. Is every `condition.type` in the closed list of thirteen?
3. Is `error_tolerance`, if used, inside `condition`?
4. Did you **run it** against a document that should fail it, and did it exit `3`?

## Reference

| File | Use it for |
| --- | --- |
| `reference/schema.md` | The closed vocabulary: conditions, providers, operations, argument keys |
| `reference/validate.md` | Checking a policy is well-formed, and the traps to check by hand |
| `reference/verdicts.md` | Running a policy, exit codes, and finding the resource behind a failure |
| `reference/terraform-plan.md` | The plan provider's operations, for OpenTofu and Terraform |
| `reference/other-providers.md` | Kubernetes, Infracost and arbitrary JSON or YAML |
| `reference/variables.md` | One policy across environments with `-var` |
| `reference/install.md` | Installing Tirith, and why the install is a git URL |
| `reference/pipelines.md` | GitHub Actions, GitLab CI, Bitbucket, Jenkins, Azure DevOps, CircleCI |
| `reference/platform.md` | Evaluating against an organization's central policies |
| `reference/debug-ci.md` | Starting from a red build and ending at the rule and the resource |

Worked policy/input pairs live in `src/tirith/tui/examples/` in the Tirith repository.
