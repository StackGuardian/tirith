Two checks combined with `&&`, and two buckets that disagree.

This is the shape most real policies take: several independent checks, joined into one
verdict by `eval_expression`.

`NotContainedIn` tests membership against a list — the value must not be any of the ACLs
named. `IsNotEmpty` catches the other common shape of misconfiguration: the attribute is
present but set to nothing, which is what an unencrypted bucket looks like in a plan.

Both checks fail, and both fail on the *same* resource: `aws_s3_bucket.public_site`. The
other bucket passes both. This is what the results view is for — the four messages are
nearly identical, and only the resource address tells you that one bucket is the problem
and the other is fine.

**Things to try**

- Change `eval_expression` to `acl_is_private || encryption_enabled`. Still fails — `||`
  needs only one to pass, and neither does.
- Set the public bucket's `acl` to `"private"`. Now `acl_is_private` passes and only the
  encryption check fails, so `&&` fails but `||` would pass.
- Add `!` to negate a check: `!acl_is_private` passes precisely when the ACL *is* public.
  Useful for writing a policy that detects a condition rather than forbidding it.
