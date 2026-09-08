# Require a tag on resources: exact

`if: field "[concat('tags[', parameters('tagName'), ']')]" exists false`, effect deny, mode Indexed.

Compliance is the key's presence in the tags map: `Contains {{ var.tagName }}` on `tags`, which
tests keys on a map (verified). Indexed mode is `error_tolerance: 2`: a type with no `tags`
attribute at all (the role assignment) is skipped.

A resource that supports tags and sets none has `"tags": null` in the plan, present but null.
`Contains` on null fails as an unsupported type, so the untagged resource is refused, which is
Azure's verdict too. `should-fail-null-tags.json` proves it.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (storage account lacks CostCenter) | deny | exit 3 |
| `should-fail-null-tags.json` (storage account has no tags at all) | deny | exit 3 |
| `should-pass.json` | pass | exit 0 |
