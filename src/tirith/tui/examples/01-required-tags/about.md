Require a costcenter tag on every resource — and watch one resource fail.

This is the smallest useful policy: one check, one condition, no operators.

`terraform_resource_type: "*"` matches every resource in the plan, and
`terraform_resource_attribute: "tags.costcenter"` reads a nested attribute — the dot
walks into the tags map. `IsNotEmpty` needs no `value`, because there is nothing to
compare against.

The plan has two resources and only `aws_instance.web` is tagged, so the policy fails.

**Things to try**

- Add `"costcenter": "product-456"` to the bucket's tags and re-run. The verdict flips.
- Add `"error_tolerance": 2` to the condition. The verdict becomes *skipped*, not passed —
  and a policy that skips every check has checked nothing. That is why `--fail-on-error`
  treats skipped as a failure rather than a pass.
- Change `IsNotEmpty` to `Equals` with `"value": "product-123"` to pin one exact value.

**A rough edge worth knowing**

The failing row has no resource address. When the provider cannot find an attribute it
reports the miss without the resource it was looking at, so the message names the
attribute but not the bucket. Results that *do* find a value carry the full address —
select the passing row to see it.
