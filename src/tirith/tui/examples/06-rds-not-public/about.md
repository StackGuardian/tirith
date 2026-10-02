A simple, single-evaluator policy to check for publicly accessible RDS instances.

This example highlights a critical security misconfiguration: a database instance that allows incoming connections from anywhere on the internet. In AWS Terraform, this is controlled by the `publicly_accessible` boolean flag on the `aws_db_instance` resource.

The policy uses a `NotEquals` condition, targeting the value `true`. If `publicly_accessible` is set to `true`, the check fails. If it is `false` (or missing/null, which defaults to false in AWS), the check passes.

The provided `input.json` contains a trimmed Terraform plan with two RDS instances:
- `aws_db_instance.private_db`, which has `publicly_accessible = false` (Passes)
- `aws_db_instance.public_db`, which has `publicly_accessible = true` (Fails)

**Things to try**

- Change `publicly_accessible` in `public_db` to `false`. The policy will now pass completely.
- Remove the `publicly_accessible` key entirely from `public_db`. The policy still passes, because a missing attribute evaluates as `null`, which is not equal to `true`.
- Change the `NotEquals` operator to `Equals` and `value` to `false`. Notice how this behaves differently: now, if `publicly_accessible` is completely missing from the plan, it might fail because `null` does not equal `false`! This is why `NotEquals: true` is often safer for boolean flags that default to false.
