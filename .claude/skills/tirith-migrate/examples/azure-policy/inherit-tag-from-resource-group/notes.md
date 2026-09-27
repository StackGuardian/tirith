# Inherit a tag from the resource group if missing: not expressible

**What it does.** Effect `modify`: when a resource lacks `tags[tagName]` and its resource group has
that tag, Azure adds the tag to the resource at deployment time.

**What Tirith cannot do.** Two things. It does not modify anything; it evaluates a document and
returns a verdict. And the `if` reads `resourceGroup().tags[...]`, the tags of a *different*
resource resolved at request time, which no attribute of the resource under evaluation carries.

**What to say to the customer.** The evaluating half of the intent is `require-tag`: refuse a
resource without the tag. The remediation half stays in Azure Policy, or moves into the Terraform
module as a `default_tags`-style local merged into every resource. `modify`, `append`,
`deployIfNotExists` and `denyAction` all land here.

No `policy.json` is shipped on purpose.
