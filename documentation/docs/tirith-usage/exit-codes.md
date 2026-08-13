---
id: exit-codes
title: Exit Codes
sidebar_label: Exit Codes
description: The complete Tirith exit-code contract, and how to gate a CI job on it.
keywords:
  - tirith
  - exit codes
  - ci
site_name: Tirith
slug: exit-codes/
---

Tirith's exit codes are a contract shared by both surfaces — local evaluation (`tirith`) and
platform evaluation (`tirith platform check`) — so a caller scripting both only has to learn one
vocabulary.

| Code | Meaning |
|---|---|
| `0` | Policies passed, or nothing was in scope to gate on |
| `1` | Tirith could not complete the evaluation — bad input, a policy it could not evaluate, unreachable API |
| `2` | Timed out waiting for a StackGuardian run (`tirith platform check` only; local evaluation never produces it) |
| `3` | A policy failed. Only with `--fail-on-error`, on either surface |
| `130` | Interrupted (Ctrl-C) |

## `3` is deliberately not `1`

`3` means a check ran and said no: your infrastructure violates a policy. `1` means Tirith could
not tell you either way — an unparseable policy file, an unresolved `{{ var.x }}` variable, an
unreachable API, or a policy whose every check was skipped. A job that treats every non-zero code
alike reports an outage as a policy violation, and cannot tell a working gate from a broken one.
Keeping the two codes distinct lets a pipeline page the platform team on `1` and the change author
on `3`.

Both surfaces **fail closed**: anything that leaves the verdict unknown exits non-zero regardless
of `--fail-on-error`. That flag governs policy verdicts, not tool health — a run that produced no
verdict must never look like a pass.

## Without `--fail-on-error`

The local command exits `0` whether the policy passed or failed, with the verdict in the output.
That is how it has always behaved, and it is left alone so that upgrading Tirith cannot turn a
passing pipeline red; the gate is opt-in. `tirith platform check` behaves the same way: without
the flag a policy failure logs a message and still exits `0`, and the verdict is in
`--output-json`.

Errors are different: a missing input file, an unparseable policy or an unresolved variable exits
`1` even without the flag.

## What each local outcome produces

Under `--fail-on-error`, the exit code is decided by the result's tri-state `final_result`:

| `final_result` | Meaning | Exit |
|---|---|---|
| `true` | every check that ran passed | `0` |
| `false` | a check ran and failed | `3` |
| `null` | every check was skipped — the policy evaluated nothing | `1` |
| absent | the policy could not be evaluated at all (for example an unresolved variable) | `1` |

`null` is not a pass. A policy whose every check was skipped — an
[`error_tolerance`](../tirith-policies/tirith-policy-error-tolerance.md) swallowing a provider that
found nothing — checked precisely nothing, and reporting that as green is exactly what the flag
exists to prevent. It is not a violation either, so it is `1` rather than `3`.

**One limit worth stating plainly:** a *misconfigured* policy — an unsupported `condition.type`,
an unknown `required_provider` — comes back from the engine as an ordinary failed check with no
error attached, so it is indistinguishable from a real violation and exits `3`. It fails closed,
which is the safe direction, but it will point at your infrastructure when the fault is in the
policy.

## Gating a CI job

Most CI systems fail a job on any non-zero exit, so the minimal gate is one line:

```sh
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

To act differently on "policy failed" versus "Tirith broke", branch on the code:

```sh
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error --json > result.json
code=$?
case "$code" in
  0) echo "policies passed" ;;
  3) echo "a policy failed — see result.json" ; exit 1 ;;
  *) echo "Tirith could not evaluate (exit $code) — this is a tooling problem, not a verdict" ; exit "$code" ;;
esac
```

The same pattern works for `tirith platform check` unchanged — the codes mean the same things.
Complete CI examples are on the [CI integration](ci-integration.md) page.
