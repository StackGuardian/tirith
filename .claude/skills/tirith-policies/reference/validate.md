# Validate a policy

## `tirith lint` is not in the released package

It is in development. The released CLI dispatches `tirith`, `tirith ui` and `tirith platform
check` and nothing else, so `tirith lint` in a pipeline you are writing for someone else is a step
that fails with an unrecognised argument.

Until it ships, validation is the two things below: check the shape against the closed vocabulary
by hand, then evaluate the policy against a document that should fail it. The second is the one
that matters, and it is the one that is available.

## Check the shape

Every trap here produces a policy that is structurally plausible and gates nothing, or that fails
for a reason unrelated to your infrastructure.

| Trap | Why it matters |
| --- | --- |
| An invented condition type | There is no `Exists`, `Matches` or `In`. The engine returns an unknown type as an ordinary failed check, so it reads as a real violation rather than a typo. |
| A key from the wrong provider | `terraform_plan` reads `terraform_resource_attribute`; `kubernetes` reads `attribute_path`. An unrecognised key is **ignored, not rejected**, so the evaluator reads nothing and the check passes. |
| An operation that does not ship | `jmespath` and `jq_query` appear in some test fixtures. Neither exists. |
| `error_tolerance` outside `condition` | It belongs **inside** `condition`. On the evaluator it is silently ignored: no warning, and the check still fails as though the tolerance were never written. |
| An evaluator nothing references | If `eval_expression` never names it, it cannot affect the verdict, however carefully it was written. |
| A single `&` where `&&` was meant | `&` and `\|` are not operators. |
| A provider that does not exist | Five ship. There is no `stackguardian/cloudformation`: a CloudFormation template is read by `stackguardian/json`. |

The closed lists are in `reference/schema.md`. Read them rather than recalling them: the cost of a
wrong key is a policy that passes everything.

## Then evaluate it

Shape is not meaning. A policy whose `provider_args` match no resource at all is structurally
perfect and gates nothing.

```bash
# Against input that SHOULD be refused. Exit 3 is the pass condition for this test.
tirith -policy-path .tirith/policies -input-path should-fail.json --fail-on-error
echo "exit: $?"
```

| Exit | Reading |
| --- | --- |
| `3` | The policy works. It refused a change it was supposed to refuse. |
| `0` | **The policy matched nothing.** Wrong provider, wrong operation, or a key the provider ignores. |
| `1` | Every check was skipped, so `final_result` is `null`. Check `error_tolerance` and whether the resource type exists in the document. |

Then run it against input that should pass, and confirm `0`. A rule only ever seen failing is as
untested as one only ever seen passing.

## Read the report rather than the summary

```bash
tirith --json -policy-path .tirith/policies -input-path plan.json > result.json
```

The JSON carries every evaluator, its result, and the value that produced it. When a check
surprises you, the value it actually read is the fastest way to the cause: an evaluator reading
`None` on every resource is the signature of a key the provider ignored.

## When lint ships

It reads the engine's own registries, so it catches the invented condition type and the
wrong-provider key from the source of truth rather than from a table that can go stale. It will
exit `3` for a bad policy and `1` for an unreadable path, matching the rest of Tirith: the linter
saying no about a policy is a verdict, not a tool failure. Check
`https://stackguardian.github.io/tirith/roadmap/` before assuming it is available.
