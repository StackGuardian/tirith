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
| `0` | Every check passed |
| `1` | Tirith could not tell you either way — bad input, an unevaluable policy, or every check skipped |
| `3` | A policy ran and said no |
| `130` | Interrupted |

`2` is argparse's usage error, so a caller seeing `2` passed a bad argument. Tirith has no timeout
code: a `platform check` that times out is reported as `1`.

**`3` is deliberately not `1`.** `3` means a check ran and refused the change. `1` means Tirith
could not reach a verdict. A job that treats every non-zero code alike reports an outage as a
policy violation and cannot tell a working gate from a broken one.

**Without `--fail-on-error` the exit code is always `0`** and the verdict is only in the output.
That is the historical behaviour, kept so upgrading cannot turn a passing pipeline red. Any real
gate needs the flag.

## A type-scoped policy refuses a plan that has none of the type

`terraform_resource_type: "aws_db_instance"` on a plan with no database is severity `1`, "resource
type not found". Under the default `error_tolerance: 0` that is a **failure, exit `3`**, so the
policy refuses every unrelated plan. With `error_tolerance: 1` it is skipped instead; if it was the
only evaluator, `final_result` is `null` and the exit is `1`. There is no setting that yields
"nothing in scope, pass" for a single-evaluator scoped policy. Choose deliberately: `1` with CI
treating exit `1` as advisory for that policy, or put several types' checks in one policy so a
skip on one leaves a verdict from the others. Not tracked as a Tirith issue at the time of writing.

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
in the safe direction, but it points at your infrastructure when the fault is in the policy.
Check the condition type against the closed list in `reference/schema.md`: a typo there is the
usual cause, and it is not reported as one.
