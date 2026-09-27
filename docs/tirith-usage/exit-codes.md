# Exit Codes

Source: https://stackguardian.github.io/tirith/docs/tirith-usage/exit-codes/
Summary: The complete Tirith exit-code contract, and how to gate a CI job on it.

Tirith's exit codes are one contract shared by every surface: local evaluation (`tirith`),
platform evaluation (`tirith platform check`), and the two file commands, `tirith lint` and
`tirith fmt`. A caller scripting more than one only has to learn a single vocabulary.

| Code | Meaning |
|---|---|
| `0` | Policies passed, nothing was in scope to gate on, or the files were clean |
| `1` | Tirith could not complete the run: bad input, a policy it could not evaluate, an unreachable API, a path that does not exist |
| `3` | A policy said no. On the evaluation surfaces only with `--fail-on-error`; `lint` and `fmt` need no flag |
| `130` | Interrupted (Ctrl-C) |

`2` is deliberately absent. It used to be a timeout code that nothing ever returned, and
`argparse` already exits `2` of its own accord on a usage error, so a caller seeing `2` has
passed a bad argument. Do not write a pipeline that branches on it.

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

## `tirith lint` and `tirith fmt`

Both use the same three codes, and neither takes `--fail-on-error`: a linter that cannot fail is
not a linter, and there is no existing green pipeline to protect because nothing has run them
before.

| Command | `0` | `3` | `1` |
|---|---|---|---|
| `tirith lint` | every policy is clean | a policy has an error-level finding, or a warning under `--strict` | a path is missing, or nothing was found to lint |
| `tirith fmt` | nothing to change, or the changes were written | `--check` found files that would change | a path is missing, a file is not valid JSON, or nothing was found |

"Nothing was found" being `1` rather than `0` is the same fail-closed rule the evaluation
surfaces follow. A hook pointed at the wrong directory reports a problem instead of quietly
passing every commit. See [lint and format](lint-and-fmt.md).

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
