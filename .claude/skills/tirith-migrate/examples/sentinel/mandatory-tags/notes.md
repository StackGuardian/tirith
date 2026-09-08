# mandatory-tags: exact

The Sentinel loops over two lists: resource types and tag keys. Tirith has no loops, so the product
is written out: one evaluator per (type, key), six in all, joined with `&&`. Verbose, but exact:
each evaluator ranges over every resource of its type, and `&&` over independently quantified
evaluators is the Sentinel `all`.

`Contains "Owner"` on the `tags` attribute tests the map's keys. Verified against the engine.
`error_tolerance: 1` skips a type that is absent from the plan.

| Plan | Sentinel | Tirith |
| --- | --- | --- |
| `should-fail.json` (instance lacks CostCenter) | fail | exit 3 |
| `should-pass.json` | pass | exit 0 |
