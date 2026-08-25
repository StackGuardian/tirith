Four checks combined with `&&`, and one resource that satisfies only half of them.

This is the shape most real policies take: several independent checks joined into one verdict by
`eval_expression`. All four have to hold, because S3 public access has four separate switches and
blocking two of them is not blocking public access.

`aws_s3_bucket_public_access_block.web` sets `block_public_acls` and `ignore_public_acls` to true
and leaves the other two false. So two evaluators pass, two fail, and `&&` fails — which is the
correct answer. A policy that only checked one attribute would have called this bucket safe.

This example previously targeted `aws_s3_bucket.acl` and an inline
`server_side_encryption_configuration` block. Both were removed in AWS provider v4, so it matched
nothing on a modern plan while still appearing to work against its own fixture — a policy that
matches nothing is the failure mode this interface exists to make visible, so shipping one as a
teaching example was the wrong lesson.

**Things to try**

- Set `block_public_policy` and `restrict_public_buckets` to `true` in the plan. All four pass and
  the verdict turns green.
- Change `eval_expression` to `block_public_acls || block_public_policy`. It passes — `||` needs
  only one, which is exactly why this policy uses `&&`.
- Add `!` to negate a check: `!block_public_policy` passes precisely when the setting is missing.
  That is how you write a detector rather than a prohibition — there is no `NotRegexMatch` or
  inverse condition, so `!` in the expression is the mechanism.
