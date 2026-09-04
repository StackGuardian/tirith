# Debug a red CI check

Start from a failed build and end at the rule and the resource. Work in this order — it is
ordered by how often each step is the answer.

## 1. Which exit code?

```bash
echo $?
```

| Exit | What it means | Where to look |
| --- | --- | --- |
| `3` | A policy ran and refused the change | Step 2 — this is a real verdict |
| `1` | No verdict was reached | Step 4 — this is not a violation |
| `0` but you expected a failure | The policy matched nothing (wrong key, wrong operation), or `--fail-on-error` is missing | Step 5 |

A job that collapses `1` and `3` will send you to step 2 for a problem that lives in step 4. Fix
the job's exit-code handling first if it does that.

## 2. Which check failed, and on which resource?

```bash
tirith --json -policy-path .tirith/policies -input-path plan.json > result.json
```

In `result.json`, find the evaluator with `"passed": false`. Each entry in its `result[]` array
carries a `meta` with the resource: `address`, `type`, and the `change` with `actions`, `before`
and `after`. Name the resource from `meta.address` rather than quoting the message — on a wildcard
policy every message reads identically.

`tirith ui --result result.json` opens the same document in an explorer, if the extra is installed.

## 3. Is the finding correct?

Read `change.after` for the address and compare it against `condition.value`. Three outcomes:

- The value really does violate the rule → fix the Terraform.
- The value is fine but the rule tests the wrong thing → fix the policy.
- The value is **absent** → the failure will arrive *without* a resource address, because there is
  no value to attach one to. Search the plan for the resource lacking that attribute.

## 4. Exit `1` — no verdict

Check `final_result` in the result document.

- **`final_result: null`** — every check was skipped, so nothing was evaluated. Almost always
  `provider_args` matching nothing. Verify the resource type is in the plan, then the attribute
  path, then whether `error_tolerance` is forgiving the very thing you meant to catch.
- **No `final_result` at all** — the policy could not be loaded. Usually an unresolved variable;
  read the `errors` array.
- **A misconfigured policy** — an unsupported `condition.type` or unknown provider arrives as an
  ordinary failed check and exits `3`, not `1`. Check `condition.type` and every `provider_args`
  key against `reference/schema.md`: an unknown key is ignored rather than rejected, so the fault
  is in the policy even though the failure points at infrastructure.

## 5. Exit `0` when you expected a failure

- Is `--fail-on-error` present? Without it the exit code is always `0` and the verdict is only in
  the output.
- Did the policy match anything? A cost policy over a misspelled `resource_type` sums to `0` and
  passes. A wildcard attribute policy with `error_tolerance: 2` skips every resource lacking the
  attribute.
- Prove the gate works by running it against a document that **should** fail it. A guardrail only
  ever seen passing is a guardrail nobody has tested.

## The two commands

```bash
tirith --json -policy-path .tirith/policies \
       -input-path plan.json | head -40            # what did it actually decide?
```
