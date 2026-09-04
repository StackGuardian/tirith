---
id: tirith-policy-packs
title: Policy Packs
sidebar_label: Policy Packs
description: Run many Tirith policies in one invocation, and the packs bundled with Tirith.
keywords:
  - tirith
  - policy pack
  - predefined policies
site_name: Tirith
slug: tirith-policy-packs/
---

A **pack** is a named set of policies that ships inside Tirith. Nothing about a packed policy is
special — each one is an ordinary Tirith policy document, run through the same engine as a file
you pass with `-policy-path`. The pack is only a name for a set, so that there is something to
type.

## Running one

```bash
tirith --list-packs
tirith --pack terraform-baseline -input-path plan.json --fail-on-error
```

`--pack` is repeatable, and combines with `-policy-path`, so your own rules run alongside the
bundled ones in a single invocation and a single verdict:

```bash
tirith --pack terraform-baseline -policy-path .tirith/policies -input-path plan.json
```

## Running a directory

`-policy-path` also accepts a directory, which is walked recursively for `*.json`:

```bash
tirith -policy-path .tirith/policies -input-path plan.json
```

## Reading the result

A run of more than one policy reports a summary rather than every policy in full:

```
104 policies · 5 passed · 2 failed · 97 skipped
Skipped policies found no resource of the type they check.

✘ 2 policy/policies failed
```

**Most policies skipping is the normal outcome, not a problem.** A check applies only to plans
that touch the resource it names, so a plan that creates one EC2 instance leaves almost every
check in a large pack with nothing to look at. Those policies are counted as `skipped`; they are
neither a pass nor a failure, and they do not affect the exit code. Failures are printed in full,
because they are the reason you ran it. `--verbose` prints every policy.

`--json` returns the aggregate document:

```json
{
  "summary": {"total": 104, "passed": 5, "failed": 2, "skipped": 97, "errored": 0},
  "final_result": false,
  "policies": [
    {"policy": "terraform-baseline/SG_TF_0042_aws_s3_bucket_versioning.json", "meta": {}, "final_result": false, "evaluators": []}
  ]
}
```

Each entry in `policies` is exactly the result document a single-policy run produces, plus a
`policy` name, so anything that already reads a Tirith result can read one of these.

A single policy **file** is unchanged: it returns the single-policy document and the exit codes it
always has. The shape follows how the run was asked for — a directory or a `--pack` is a set — not
how many policies happened to match, so a directory holding one policy still reports as a set.

## Exit codes

With `--fail-on-error`:

| Situation | Code |
|---|---|
| At least one policy failed | `3` |
| No failures, at least one policy reached a verdict | `0` |
| Nothing ran, or every policy skipped | `1` |

Skipped policies never produce `3`. A pack whose policies all skipped exits `1`, on the same rule
the single-policy path applies to `final_result: null`: nothing was checked, so nothing can be
reported as green.

## Bundled packs

| Pack | Policies | Scope |
|---|---|---|
| `terraform-baseline` | 104 | Baseline security and configuration checks for Terraform plans, across AWS, Azure, GCP, Kubernetes and several smaller providers |

Every policy in a bundled pack has been verified end to end: it passes a compliant document and
fails a violating one, and those fixtures are run in Tirith's own CI, so an engine change cannot
silently turn a check into a no-op.

### Identifiers and tags

Packed policies carry a StackGuardian id — `SG_TF_0042` — that is allocated once and never
reassigned, so a report can name a check and mean the same check next release. `meta.tags` carry a
`cloud:<name>` tag plus the policy's category, and are the seam that compliance-framework tags
will slot into.
