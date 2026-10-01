# Allowed locations: exact

`if: allOf [location notIn P, location notEquals global, type notEquals b2cDirectories]`, effect from
a parameter, mode Indexed. Violation when the location is outside the list and is not `global`.

Compliance is `location ContainedIn P`. `global` is appended to the list in `variables.json`, which
is what Azure's second leaf does. The third leaf exempts one type that has no Terraform resource.
Indexed mode is `error_tolerance: 2` over `*`: a resource type with no `location`, the role
assignment in both plans, is skipped rather than failed.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (a VM in eastus) | deny | exit 3 |
| `should-pass.json` | pass | exit 0 |

`listOfAllowedLocations` has no default in the definition. The value comes from the assignment.
