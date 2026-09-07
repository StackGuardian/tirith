# Worked example: a naming standard that stays green on unrelated changes

One policy and three plans. It exists to demonstrate the shape every type-scoped standards
policy needs, because the obvious version of this policy is red on most pull requests.

| File | |
| --- | --- |
| `naming.json` | `RegexMatch` on `aws_s3_bucket.bucket`, guarded by a `count` evaluator |
| `should-fail.json` | Two buckets, one named `my-logs-bucket`. Expect exit `3` |
| `should-pass.json` | The same two buckets, both named to convention. Expect exit `0` |
| `no-bucket.json` | A plan that touches only an EC2 instance. Expect exit `0` |

```bash
cd .claude/skills/tirith-standards/examples/org-standards
for doc in should-fail should-pass no-bucket; do
  tirith -policy-path naming.json -input-path "$doc.json" --fail-on-error >/dev/null 2>&1
  echo "$doc -> exit $?"
done
# should-fail -> exit 3
# should-pass -> exit 0
# no-bucket   -> exit 0
```

## Why the guard is there

A policy scoped to one resource type has no green outcome on a plan that does not touch that
type. Both settings are red, in different ways:

| `error_tolerance` | Plan has no bucket | Reads as |
| --- | --- | --- |
| omitted, so `0` | severity `1` is greater than `0`, so the check **fails**, exit `3` | your infrastructure violates a policy |
| `1` | the check is **skipped**, every check is skipped, `final_result` is `null`, exit `1` | Tirith could not reach a verdict |

Neither is what you want on a pull request that only edits a Lambda.

The guard fixes it because `count` behaves differently from `attribute` on an absent type: it
returns `0` rather than raising severity `1`. So `no_bucket_in_this_plan` evaluates cleanly to
`true`, the naming check is skipped and dropped from the expression, and

```
no_bucket_in_this_plan || bucket_name_matches_convention
```

is `true`. On a plan that does have buckets the guard is `false` and the naming check decides.

`error_tolerance: 1` stays on the naming evaluator so that in the no-bucket case it is *skipped*
rather than *failed and then masked by the guard*. Both produce exit `0` here, but a failure
hidden behind an `||` shows up in `--json` output and in the printed result, and a reader
debugging the policy later should not have to work out whether that failure mattered.

## Things to try

- Delete the guard evaluator and set `eval_expression` to the naming check alone. `no-bucket.json`
  now exits `1` with `final_result: null`.
- Delete the guard *and* the `error_tolerance`. `no-bucket.json` now exits `3`, reporting a
  policy violation for a plan containing nothing the policy is about.
- Change `RegexMatch` to `Matches`. It does not exist. The run exits `3` with `errors` empty, so
  CI sees a violation and only the message says the evaluator is unsupported.
- Add a bucket using `bucket_prefix` instead of `bucket` to `should-pass.json`. The name is not
  known at plan time, arrives as `null`, and fails the regex. This is the trap named in
  `meta.description`.
