A single check for publicly accessible databases, and two instances that disagree.

Databases holding production data should rarely accept connections from the open internet. In AWS Terraform, whether an `aws_db_instance` is reachable from outside its VPC is governed by the `publicly_accessible` boolean flag.

`NotEquals` tests that the attribute is anything other than `true`. If `publicly_accessible` is set to `true`, the check fails. If set to `false` (or omitted, which defaults to private in AWS), the check passes.

The input plan contains two database instances:
- `aws_db_instance.private_db`, configured with `publicly_accessible = false` (passes).
- `aws_db_instance.public_db`, configured with `publicly_accessible = true` (fails).

Because one instance violates the policy, the overall evaluation fails. In the results view, notice how the resource address immediately identifies which instance caused the failure.

**Things to try**

- In `input.json`, change `public_db`'s `publicly_accessible` to `false`. Re-evaluate and watch the verdict turn green.
- Remove `publicly_accessible` from `public_db` entirely. The check still passes because missing attributes evaluate to `null`, which is not equal to `true`.
- In `policy.json`, change `NotEquals` with `true` to `Equals` with `false`. See what happens when `publicly_accessible` is omitted — `null` does not equal `false`, showing why `NotEquals: true` is often the safer choice for boolean security flags.
