# Secure transfer to storage accounts should be enabled: exact

`if: allOf [type equals storageAccounts, anyOf [allOf [apiVersion less 2019-04-01, supportsHttpsTrafficOnly exists false], supportsHttpsTrafficOnly equals false]]`.

The API-version branch is a request-time expression with no plan counterpart and is dropped; on
the current API the property always exists, so compliance is `supportsHttpsTrafficOnly Equals true`.

azurerm renamed the attribute in 4.0: `https_traffic_only_enabled`, previously
`enable_https_traffic_only`. Two evaluators, one per name, each at `error_tolerance: 2` so the
absent name is skipped, joined with `||`. Whichever name the plan carries decides.

`arm/` holds the same policy for an ARM template on the json provider, in the corpus's type-guard
idiom: `no_storage_account || https_only`. A template without a storage account passes
(`should-pass-no-storage.json`); one with the property false, or absent, fails.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (4.x name, false) | audit | exit 3 |
| `should-fail-azurerm3.json` (3.x name, false) | audit | exit 3 |
| `should-pass.json` | pass | exit 0 |
| `arm/should-fail.json`, `arm/should-pass.json`, `arm/should-pass-no-storage.json` | | 3, 0, 0 |

Effect is `audit`: `meta.enforcement` says so, and the CLI cannot make it advisory. Run audit
policies in their own directory and decide what exit 3 means for that run.
