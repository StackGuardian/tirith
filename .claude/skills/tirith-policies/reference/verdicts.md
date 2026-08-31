# Run a policy and read the verdict

```bash
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
echo $?
```

`-policy-path` takes a file or a directory. `-input-path` takes the document the provider expects.
Add `--json` to get the result document instead of the pretty printer.

## Exit codes are a contract

| Exit | Meaning |
| --- | --- |
| `0` | Policies passed, or nothing was in scope to gate on |
| `1` | Tirith could not tell you either way — bad input, an unevaluable policy, or every check skipped |
| `2` | Timed out waiting for a StackGuardian run (`platform check` only) |
| `3` | A policy ran and said no |
| `130` | Interrupted |

**`3` is deliberately not `1`.** `3` means a check ran and refused the change. `1` means Tirith
could not reach a verdict. A job that treats every non-zero code alike reports an outage as a
policy violation and cannot tell a working gate from a broken one.

**Without `--fail-on-error` the exit code is always `0`** and the verdict is only in the output.
That is the historical behaviour, kept so upgrading cannot turn a passing pipeline red. Any real
gate needs the flag.

## `final_result: null` is not a pass

It means **every check was skipped** — nothing was evaluated. Under `--fail-on-error` that exits
`1`, not `0` and not `3`.

It almost always means `provider_args` matched nothing. Check, in this order:

1. `terraform_resource_type` — is that type actually in the plan?
2. The attribute path — is it under `change.after`, and spelled as the plan spells it?
3. `error_tolerance` — is it forgiving the very problem you wanted to catch?

Do not reach for the condition until the provider is returning values.

## Reading the result document

`--json` returns `final_result`, an `evaluators[]` array, `errors`, and the `eval_expression` that
was evaluated. Each evaluator carries `passed` (`true`, `false`, or `null` for skipped) and a
`result[]` of individual findings.

Each finding's `meta` carries the resource behind it: `address`, `type`, `name`, and the `change`
with `actions`, `before`, `after` and `after_unknown`. That is how you name the resource that
failed rather than only quoting the message.

**One asymmetry:** when a check fails because an attribute is *absent*, there is no value to
attach a resource to, so the failure arrives **without a resource address**. Find the culprit by
looking in the plan for the resource lacking that attribute.

## A misconfigured policy fails closed

An unsupported `condition.type` or an unknown `required_provider` comes back as an ordinary failed
check with no error attached — indistinguishable from a real violation, and it exits `3`. It fails
in the safe direction, but it points at your infrastructure when the fault is in the policy. Run
`tirith lint` first and this class disappears.
