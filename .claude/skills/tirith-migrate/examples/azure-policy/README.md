# Azure Policy migrations

Eight built-ins from `Azure/azure-policy`, chosen because they are the ones a customer assigns
first and because the public corpus skipped them (parameter-driven, or untyped). Each directory has
`source.json` (the definition, verbatim), `notes.md`, and for a translation `policy.json` with
`should-fail.json` and `should-pass.json`. Parameterised ones add `variables.json`; approximate ones
add `diverges.json`.

```bash
cd allowed-locations
tirith -policy-path policy.json -input-path should-fail.json --fail-on-error -var-path variables.json; echo $?   # 3
tirith -policy-path policy.json -input-path should-pass.json --fail-on-error -var-path variables.json; echo $?   # 0
```

| Example | Effect, mode | Fidelity | Shows |
| --- | --- | --- | --- |
| `allowed-locations` | deny, Indexed | exact | `notIn` to `ContainedIn`; Indexed mode is `error_tolerance: 2`; a role assignment is skipped |
| `require-tag` | deny, Indexed | exact | `tags['x'] exists false` to `Contains` on the map; `tags: null` fails |
| `not-allowed-resource-types` | deny, All | exact | `count` `Equals 0` per forbidden type; one Azure type is three azurerm types |
| `allowed-resource-types` | deny, Indexed | approximate | `count` over `*` with the allow-list excluded; non-Azure resources must be excluded by hand |
| `allowed-vm-skus` | deny, Indexed | exact | `sku.name` is `size` or `vm_size`; three evaluators, `&&` |
| `storage-secure-transfer` | audit, Indexed | exact | provider version rename handled with `\|\|`; an ARM version in `arm/` shows the json type guard |
| `nsg-rdp-from-internet` | audit, All | approximate | four tests on one rule cannot be bound; `diverges.json` shows the stricter verdict |
| `inherit-tag-from-resource-group` | modify | not expressible | refused in words |
