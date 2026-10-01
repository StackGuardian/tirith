# Not allowed resource types: exact

`if: allOf [type in P, value "[field('type')]" exists true]`, mode All. The second leaf is an ARM
expression that is always true; it exists to make the definition well-formed and is dropped.

Compliance is "no resource of any forbidden type": operation `count` per type, `Equals 0`. `count`
returns `0` for a type absent from the plan (verified), so no tolerance is needed. One Azure type is
often several azurerm types: `Microsoft.Compute/virtualMachines` is `azurerm_virtual_machine`,
`azurerm_linux_virtual_machine` and `azurerm_windows_virtual_machine`. A `-var` cannot feed
`terraform_resource_type`, so the assignment's list is written out.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (a public IP) | deny | exit 3 |
| `should-pass.json` | pass | exit 0 |
