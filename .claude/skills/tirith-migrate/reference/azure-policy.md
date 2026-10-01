# Azure Policy to Tirith

An Azure Policy definition is a JSON document whose `properties.policyRule` has an `if` tree of
`{field, operator, value}` leaves under `allOf` / `anyOf` / `not`, and a `then.effect`. That is
structurally a Tirith policy: `field` is the attribute, the operator is the condition, the logic is
`eval_expression`. Two things make the translation more than a rename, and both are decided first.

## 1. Polarity: `if` describes the violation

Azure fires the effect when `if` matches. A Tirith evaluator describes compliance. So every leaf is
translated to its **opposite**, and the logic flips with it:

| `if` leaf (violation) | Tirith condition (compliance) |
| --- | --- |
| `equals X` | `NotEquals X` |
| `notEquals X` | `Equals X` |
| `in [..]` | `NotContainedIn [..]` |
| `notIn [..]` | `ContainedIn [..]` |
| `contains X` | `NotContains X` |
| `notContains X` | `Contains X` |
| `containsKey K` (on a map, e.g. tags) | `NotContains K` on the map. `Contains` on a map tests its keys, verified |
| `notContainsKey K` | `Contains K` |
| `exists: "false"` | `IsNotEmpty` |
| `exists: "true"` | `IsEmpty` |
| `less N` | `GreaterThanEqualTo N` |
| `lessOrEquals N` | `GreaterThan N` |
| `greater N` | `LessThanEqualTo N` |
| `greaterOrEquals N` | `LessThan N` |
| `like "a*"` | `RegexMatch "^a.*$"` and `!` in the expression. `*` is the only wildcard |
| `notLike "a*"` | `RegexMatch "^a.*$"` |
| `match`, `notMatch`, `matchInsensitively`, `notMatchInsensitively` | not expressible: `#` digit, `?` letter, `.` any is not a regex. Hand-translate the pattern to a regex and mark approximate |

| `if` logic | Tirith | Fidelity |
| --- | --- | --- |
| `{field: type, equals: T}` inside an `allOf` | scope: `terraform_resource_type` (or the json type guard) | exact |
| `anyOf [A, B]` (violation if either) | `notA && notB` | exact |
| `not X` | `X` translated positively | exact |
| `allOf [A, B]` on two attributes of the same resource (violation only if both) | `notA \|\| notB` | approximate, stricter: Tirith cannot bind both tests to one resource. Issue #316 |
| `count { field: X[*], where: {...} } greater 0` | wildcard path over `X.*.` where the inner test is one attribute | approximate; a `where` on two attributes is not expressible |
| `{value: "[...]", ...}` (an ARM expression, `requestContext()`, `resourceGroup()`, `field()` arithmetic) | none | not expressible |

Most built-ins are `allOf [{type equals T}, {one field test}]`: scope plus one leaf, which is exact.

## 2. Target: Terraform plan or ARM template

| Target | Provider | When |
| --- | --- | --- |
| Terraform (`azurerm`) | `stackguardian/terraform_plan` | The team writes Terraform. Attribute names come from the crosswalk below; one Azure type is often two or three azurerm types |
| ARM template | `stackguardian/json` | The team deploys ARM or Bicep-built JSON. Paths come from the alias rule below; every translation is approximate because the json provider scopes the document, not the resource |

### Terraform: alias to azurerm attribute

Verified: each row is an attribute a corpus policy evaluates end to end against a plan.

| Azure alias | azurerm resource | attribute |
| --- | --- | --- |
| `location` (any type) | `*` | `location`, `error_tolerance: 2` |
| `tags['K']`, `tags.K` | `*` | `tags` with `Contains "K"`, `error_tolerance: 2` |
| `type` in `[..]` (Not allowed resource types) | each forbidden type | operation `count`, `Equals 0` |
| `type` not in `[..]` (Allowed resource types) | `*` with `exclude_resource_types` = allowed | operation `count`, `Equals 0` |
| `Microsoft.Compute/virtualMachines/sku.name` | `azurerm_linux_virtual_machine`, `azurerm_windows_virtual_machine` | `size`; legacy `azurerm_virtual_machine` uses `vm_size` |
| `Microsoft.Compute/virtualMachines/securityProfile.encryptionAtHost` | `azurerm_linux_virtual_machine`, `azurerm_windows_virtual_machine`, both scale sets | `encryption_at_host_enabled` |
| `Microsoft.Compute/virtualMachines/osProfile.linuxConfiguration.disablePasswordAuthentication` | `azurerm_linux_virtual_machine` | `disable_password_authentication` |
| `Microsoft.Storage/storageAccounts/supportsHttpsTrafficOnly` | `azurerm_storage_account` | `https_traffic_only_enabled` (4.x), `enable_https_traffic_only` (3.x) |
| `Microsoft.Storage/storageAccounts/minimumTlsVersion` | `azurerm_storage_account` | `min_tls_version`, values `TLS1_2`, `TLS1_3` |
| `Microsoft.Storage/storageAccounts/allowBlobPublicAccess` | `azurerm_storage_account` | `allow_nested_items_to_be_public` (3.x+), `allow_blob_public_access` (2.x) |
| `Microsoft.Storage/storageAccounts/networkAcls.defaultAction` | `azurerm_storage_account` | `network_rules.*.default_action` |
| `Microsoft.Storage/storageAccounts/encryption.requireInfrastructureEncryption` | `azurerm_storage_account` | `infrastructure_encryption_enabled` |
| `Microsoft.Storage/storageAccounts/blobServices/containers/publicAccess` | `azurerm_storage_container` | `container_access_type`, compliant `private` |
| `Microsoft.KeyVault/vaults/enablePurgeProtection` | `azurerm_key_vault` | `purge_protection_enabled` |
| `Microsoft.KeyVault/vaults/enableSoftDelete` | `azurerm_key_vault` | `soft_delete_retention_days` (soft delete is always on in 3.x+) |
| `Microsoft.KeyVault/vaults/networkAcls.defaultAction` | `azurerm_key_vault` | `network_acls.*.default_action` |
| `Microsoft.Web/sites/httpsOnly` | `azurerm_linux_web_app`, `azurerm_windows_web_app`, `azurerm_app_service`, slots | `https_only` |
| `Microsoft.Web/sites/config/minTlsVersion` | same | `site_config.*.minimum_tls_version` (`min_tls_version` on `azurerm_app_service`) |
| `Microsoft.Web/sites/publicNetworkAccess` | same | `public_network_access_enabled` |
| `Microsoft.Sql/servers/minimalTlsVersion` | `azurerm_mssql_server` | `minimum_tls_version` |
| `Microsoft.Sql/servers/publicNetworkAccess` | `azurerm_mssql_server` | `public_network_access_enabled` |
| `Microsoft.DBforPostgreSQL/servers/sslEnforcement`, `minimalTlsVersion` | `azurerm_postgresql_server` | `ssl_enforcement_enabled`, `ssl_minimal_tls_version_enforced` |
| `Microsoft.DBforMySQL/servers/minimalTlsVersion` | `azurerm_mysql_server` | `ssl_minimal_tls_version_enforced` |
| `Microsoft.ContainerService/managedClusters/apiServerAccessProfile.enablePrivateCluster` | `azurerm_kubernetes_cluster` | `private_cluster_enabled` |
| `Microsoft.ContainerService/managedClusters/aadProfile.enableAzureRBAC` | `azurerm_kubernetes_cluster` | `azure_active_directory_role_based_access_control.*.azure_rbac_enabled` |
| `Microsoft.ContainerService/managedClusters/agentPoolProfiles[*].enableNodePublicIP` | `azurerm_kubernetes_cluster` | `default_node_pool.*.enable_node_public_ip` |
| `Microsoft.ContainerRegistry/registries/publicNetworkAccess` | `azurerm_container_registry` | `public_network_access_enabled` |
| `Microsoft.ContainerRegistry/registries/networkRuleSet.defaultAction` | `azurerm_container_registry` | `network_rule_set.*.default_action` |
| `Microsoft.Network/networkSecurityGroups/securityRules/*` | `azurerm_network_security_rule` | `direction`, `access`, `destination_port_range`, `source_address_prefix`; inline rules are `security_rule.*.<name>` on `azurerm_network_security_group` |
| `Microsoft.Cache/redis/minimumTlsVersion` | `azurerm_redis_cache` | `minimum_tls_version` |
| `Microsoft.EventHub/namespaces/minimumTlsVersion` | `azurerm_eventhub_namespace` | `minimum_tls_version` |
| `Microsoft.ServiceBus/namespaces/minimumTlsVersion` | `azurerm_servicebus_namespace` | `minimum_tls_version` |
| `*/publicNetworkAccess` on most PaaS types | the azurerm type | `public_network_access_enabled` |
| `Microsoft.Network/networkInterfaces/enableIPForwarding`, publicIPs on NICs, resource-group-level anything | | not expressible: no single attribute carries it |

An attribute the plan leaves unset arrives as `null` in `change.after`, not absent. `Equals` and
`ContainedIn` fail it cleanly; `Contains` fails it as an unsupported type; `IsNotEmpty` fails it.
A key the type does not have at all is absent and is what `error_tolerance: 2` skips.

### ARM: alias to JSON path

The rule, validated in the corpus against 36 independently verified paths: strip the resource type
(the whole `Namespace/type/childType/`, not one segment), turn `[*]` into `.*`, join with `.`,
prefix `properties.` unless the first segment is an envelope key (`sku`, `identity`, `tags`,
`location`, `zones`, `plan`, `kind`, `managedBy`, `name`, `type`, `id`). `type`, `name`, `location`,
`kind`, `identity.type` and `tags...` stay as they are.

The json provider cannot scope by resource type (issue #317), so every ARM translation uses the
**type guard** and is approximate:

```json
{"id": "no_such_type",
 "provider_args": {"operation_type": "get_value", "key_path": "resources.*.type"},
 "condition": {"type": "NotContainedIn", "value": ["Microsoft.Storage/storageAccounts", "microsoft.storage/storageaccounts"], "error_tolerance": 2}}
```

with `"eval_expression": "no_such_type || the_check"`. A template with no such type passes; once
the type is present anywhere, the attribute path is read across **every** resource in the template,
so a second resource type that happens to carry the same property name is swept in. ARM type strings
are case-insensitive in Azure and compared exactly here; list the spellings you expect. Use the guard
only when Azure fails on an absent property (`notEquals`, `exists: false`): it turns absence into
failure at every inner tolerance.

## 3. Effects

| `then.effect` | Tirith | Fidelity |
| --- | --- | --- |
| `deny` | `meta.enforcement: "deny"`, run with `--fail-on-error` | exact |
| `audit` | `meta.enforcement: "audit"`. The CLI has no advisory tier: keep audit policies in their own directory and do not gate the job on their exit, or treat exit 3 from that run as a warning | approximate |
| `disabled` | do not translate | |
| `[parameters('effect')]` | the assignment decides; record the allowed values in the notes and pick the assignment's | |
| `auditIfNotExists`, `deployIfNotExists` | asserts a *related* resource exists, from `then.details`, not from `if`. `direct_references` with `referenced_by` covers "every X is referenced by a Y" at type level; anything on the related resource's attributes is not expressible | approximate or not expressible |
| `modify`, `append`, `denyAction`, `manual` | remediation or process, not evaluation | not expressible |

## 4. Modes and parameters

- **`mode: Indexed`** means Azure evaluates only resource types that support tags and location.
  Translate with `error_tolerance: 2` on `location` or `tags` over `terraform_resource_type: "*"`,
  which skips the types that lack the attribute. **`mode: All`** includes everything, including
  resource groups and subscriptions, which Terraform models as resources too.
- **`[parameters('x')]`** becomes `{{ var.x }}` with a `variables.json` beside the policy. The
  definition often has no `defaultValue`; the value lives in the **assignment**. Ask for it, or
  read `properties.parameters` on the assignment. A parameter feeding `terraform_resource_type` or
  `exclude_resource_types` cannot be a `-var`: write the types out, one evaluator per type.
- **`[concat('tags[', parameters('tagName'), ']')]`** is the `tags` attribute with `Contains {{ var.tagName }}`.
- **Initiatives** (policy set definitions) are a directory of policies. **Assignments**, scopes and
  exemptions have no counterpart: a Tirith policy applies to whatever plan it is run against.

## 5. What to expect

Measured on HashiCorp-style public data, this time Microsoft's own `Azure/azure-policy` repository,
by the tirith-policy-corpus project (ARM target, json provider):

| | count |
| --- | --- |
| Definitions with an asserting effect (`audit` or `deny`) | 713 |
| Translated to Tirith | 376, all approximate (document scope) |
| Blocked | 110 |
| Not started | 227 |

Why blocked, in order: `mode: Microsoft.Kubernetes.Data` (Gatekeeper constraints inside a live
cluster, not ARM); a per-resource disjunction over two attribute sets chosen by API version (T5);
per-resource scoping on a sibling attribute (T18, issue #316); a comparison value that is an
assignment-time parameter with no default (T19, translatable once the assignment supplies it);
`count` with a `where` over two attributes (T9); value expressions and arithmetic (T10, issue #338).

The built-ins a customer assigns first, Allowed locations, Require a tag, Allowed and Not allowed
resource types, Allowed VM SKUs, are all parameter-driven and untyped, so the corpus skipped them.
They translate cleanly to the Terraform target; `examples/azure-policy/` has each one verified.

`reference/azure-policy-corpus.md` lists the 376 translated and 110 blocked definitions by GUID and
display name, with the corpus path or the blocking reason. Look a built-in up there before
translating it; if it is translated, the ARM version exists and the Terraform version is a
crosswalk away.

## 6. Verifying

Azure definitions ship no test fixtures. Write a plan by hand: `terraform show -json` shape, one
`resource_changes` entry per resource, the attribute under `change.after`. Include one resource of a
type the policy does not cover, so the run proves the scope. For `Indexed` translations include a
type without `location` or `tags` (a role assignment) and confirm it is skipped, not failed. Expect
exit `3` on the violating plan and `0` on the compliant one, and for every approximate row a
`diverges.json` where Azure and Tirith disagree.
