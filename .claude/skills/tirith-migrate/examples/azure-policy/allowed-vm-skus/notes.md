# Allowed virtual machine size SKUs: exact

`if: allOf [type equals Microsoft.Compute/virtualMachines, not {sku.name in P}]`, effect Deny.

The type leaf is scope; the `not in` becomes `ContainedIn`. `sku.name` is `size` on
`azurerm_linux_virtual_machine` and `azurerm_windows_virtual_machine` and `vm_size` on the legacy
`azurerm_virtual_machine`: three evaluators joined with `&&`, each at `error_tolerance: 1` so a plan
without one of the three types is not refused for it.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (Standard_E64s_v5) | deny | exit 3 |
| `should-pass.json` (a Linux and a Windows VM, both allowed) | pass | exit 0 |
