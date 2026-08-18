Budget gates over an Infracost report, with a total and a per-service ceiling.

A different provider and a different input document: this reads
`infracost breakdown --format json`, not a terraform plan.

`resource_type` here is a **list**, unlike the terraform provider's plain string.
`["*"]` totals the whole plan; naming types instead sums only those. The two checks show
both: `$388.47` across everything, `$181.77` for the two `aws_instance` resources.

Both pass, so the policy passes.

**Things to try**

- Lower the total budget to `300`. The first check fails and the verdict flips.
- Set `resource_type` to `["aws_rds_cluster"]` to gate the database separately.
- Note there are no resource addresses in the results. Infracost sums across resources, so
  a cost check reports one number with no single resource behind it — unlike the terraform
  examples, where every result names its resource.

**A rough edge worth knowing**

Matching is on the exact resource *type* — the part of the name before the first dot — so
`["aws_instance"]` matches `aws_instance.app_server`, but a partial type like `["aws_s3"]`
matches nothing and silently sums to `0`. A cost check that suddenly reads `0` is usually a
misspelled type rather than a free plan, and because `0` passes every `LessThanEqualTo`
ceiling, it fails open. Name types exactly.
