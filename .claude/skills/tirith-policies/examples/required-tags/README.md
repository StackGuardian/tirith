# Worked example: every resource carries a costcenter tag

One policy and two plans. Use it to confirm Tirith is installed and to see what a working
policy looks like before writing your own.

| File | |
| --- | --- |
| `policy.json` | `IsNotEmpty` on `tags.costcenter` across every resource type |
| `should-fail.json` | Two resources, one without the tag. Expect exit `3` |
| `should-pass.json` | The same plan with both resources tagged. Expect exit `0` |

```bash
cd .claude/skills/tirith-policies/examples/required-tags
tirith -policy-path policy.json -input-path should-fail.json --fail-on-error; echo "exit: $?"   # 3
tirith -policy-path policy.json -input-path should-pass.json --fail-on-error; echo "exit: $?"   # 0
```

Copy the pair when testing a new policy: edit `policy.json` to the rule you want, then change
`should-fail.json` until it violates it. A rule that has only ever been seen passing is untested.

Things to try:

- Add `"error_tolerance": 2` inside `condition` and run against `should-fail.json`. The check is
  skipped rather than failed, `final_result` becomes `null`, and the exit is `1`, not `0`.
- Change `IsNotEmpty` to `Equals` with `"value": "product-123"` to pin one exact value.
- Change the type to `Exists`. It does not exist, and the run exits `3` with no error attached,
  which is why an unknown condition type reads like a real violation.
