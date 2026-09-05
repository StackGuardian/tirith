# restrict-ssh-ingress: approximate, stricter

The Sentinel binds three tests to the same ingress block: port range covers 22, and cidr is
`0.0.0.0/0`. Tirith evaluators are per resource and `eval_expression` combines verdicts already
collapsed across all resources, so nothing can say "the block where both hold". The translation
keeps the test that carries the intent, `0.0.0.0/0` in any ingress block, and drops the port.

The result is stricter: a group that opens 443 to the world and 22 to the VPC passes Sentinel
and fails Tirith. Issue #316 (`resource_filter`) would make this exact.

| Plan | Sentinel | Tirith |
| --- | --- | --- |
| `should-fail.json` (22 from anywhere) | fail | exit 3 |
| `should-pass.json` (everything internal) | pass | exit 0 |
| `diverges.json` (443 from anywhere, 22 internal) | **pass** | **exit 3** |

`error_tolerance: 2` skips a group with no ingress blocks, which Sentinel's `any` also passed. A
skipped group next to the bastion leaves the bastion's failure standing: exit `3`.
