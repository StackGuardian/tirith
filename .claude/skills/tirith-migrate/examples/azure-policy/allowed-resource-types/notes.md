# Allowed resource types: approximate

`if: not {type in P}`, mode Indexed. Violation when a resource's type is outside the allow-list.

No operation yields a resource's type as a value, so the test is inverted onto `count`: over `*`
with `exclude_resource_types` set to the allow-list, the count of everything else must be `0`
(verified: `exclude_resource_types` is honoured by `count`).

Approximate for two reasons. Azure sees only Azure resources; a Terraform plan also holds
`random_id`, `null_resource`, data sources and other providers' resources, and each counts as a
violation unless excluded by hand, as `random_id` is here. And the allow-list must name azurerm
types, so one Azure type expands to several rows.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (a VM outside the list) | deny | exit 3 |
| `should-pass.json` (with a `random_id`, excluded) | pass | exit 0 |
