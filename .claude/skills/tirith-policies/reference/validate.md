# Validate a policy

## `tirith lint` checks the shape

This is the one place in the pack that explains it; the other files point here.

```bash
tirith lint .tirith/policies
```

It reads the live `EVALUATORS_DICT` and `PROVIDERS_DICT` registries, so it catches every trap in
the table below except the ones only evaluation can catch. Exit `3` when a policy has an error,
`1` when a path is missing or nothing was found, `0` when clean. `--strict` counts warnings as
errors, `--json` emits the findings as a document.

With no path it lints `.tirith/policies` if that directory exists, otherwise the current
directory. JSON that is not a policy is skipped, so pointing it at a directory holding plan
documents is safe.

**It is not in 1.2.0.** `tirith lint` and `tirith fmt` are on `main` and arrive in the next
release. Install `@main` rather than the tag if you want them now:
`pip install "git+https://github.com/StackGuardian/tirith.git@main"`.

`tirith fmt` rewrites a policy into the canonical layout, and `tirith fmt --check` exits `3` if
a file would change. Neither command needs a plan document, which is why both work in a
pre-commit hook.

## The same validator, interactively

`tirith ui` carries the one `tirith lint` calls. The Playground runs it on every keystroke while
the Builder refuses to add a check that fails it:

```bash
pip install 'py-tirith[tui] @ git+https://github.com/StackGuardian/tirith.git'
tirith ui --policy .tirith/policies/my-policy.json
```

It is advisory by design: it reports a malformed policy rather than refusing to evaluate it,
because experimenting with a half-written policy is the point of a playground.

## Without either command

Pinned to `1.2.0` and unable to install `@main`? Check the shape against the closed vocabulary by
hand, then evaluate the policy against a document that should fail it. The second is the one that
matters, and it works on every version.

## Check the shape

Every trap here produces a policy that is structurally plausible and gates nothing, or that fails
for a reason unrelated to your infrastructure.

| Trap | Why it matters |
| --- | --- |
| An invented condition type | There is no `Exists`, `Matches` or `In`. The engine returns an unknown type as a failed check, exit `3`, `errors` empty. The result message does name it; the exit code does not. |
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

`examples/required-tags/` in this pack has a policy with a failing and a passing plan. Copy the
pair and edit it rather than starting from an empty file.

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
