---
id: sg-workflow-provider
title: SG Workflow Provider
sidebar_label: SG Workflow
description: Reference for the stackguardian/sg_workflow provider - supported workflow attributes, return shapes, and error behavior.
keywords:
  - tirith
site_name: Tirith
slug: sg-workflow-provider/
---

```
required_provider: stackguardian/sg_workflow
```

Reads attributes of a StackGuardian workflow definition.

## Input document

A StackGuardian workflow definition in JSON form — the object that contains keys such as `WfType`, `TerraformConfig`, `VCSConfig`, and `DeploymentPlatformConfig`.

## Parameters

This provider does not dispatch on `operation_type`. It reads exactly one key from `provider_args`:

| Parameter | Required | Description |
|---|---|---|
| `workflow_attribute` | yes | The name of the workflow attribute to read (see the table below). |

By convention policies also set `"operation_type": "attribute"` (the test fixtures do), but the provider does not read or validate that key.

## Supported values for `workflow_attribute`

The attribute name determines where in the workflow document the value is read from:

| `workflow_attribute` | Read from | Typical shape |
|---|---|---|
| `integrationId` | `DeploymentPlatformConfig[].config.integrationId`, with the `/integrations/` prefix stripped from each id | list of strings |
| `Description` | top level | string |
| `DocVersion` | top level | string |
| `ResourceName` | top level | string |
| `ResourceType` | top level | string (e.g. `WORKFLOW`) |
| `Tags` | top level | list of strings |
| `WfType` | top level | string (e.g. `TERRAFORM`) |
| `approvalPreApply` | `TerraformConfig` | boolean |
| `driftCheck` | `TerraformConfig` | boolean |
| `managedTerraformState` | `TerraformConfig` | boolean |
| `terraformVersion` | `TerraformConfig` | string |
| `bucket_region` | `VCSConfig.iacInputData.data` | string |
| `s3_bucket_acl` | `VCSConfig.iacInputData.data` | string |
| `s3_bucket_block_public_acls` | `VCSConfig.iacInputData.data` | boolean |
| `s3_bucket_block_public_policy` | `VCSConfig.iacInputData.data` | boolean |
| `s3_bucket_force_destroy` | `VCSConfig.iacInputData.data` | boolean |
| `s3_bucket_ignore_public_acls` | `VCSConfig.iacInputData.data` | boolean |
| `s3_bucket_restrict_public_buckets` | `VCSConfig.iacInputData.data` | boolean |
| `iacTemplateId` | `VCSConfig.iacVCSConfig` | string |
| `useMarketplaceTemplate` | `VCSConfig.iacVCSConfig` | boolean |

**Returns:** a single value with the shape shown above. `integrationId` returns a list — pair it with `Contains` (see the example) rather than `Equals`.

**On a miss / error:** all errors from this provider carry **no severity value**, so they always fail the check and `error_tolerance` cannot skip them:

- The attribute's containing key is absent from the workflow document (e.g. no `TerraformConfig` when asking for `driftCheck`) — error `'<attribute> not found in input_data'`.
- `workflow_attribute` missing from `provider_args` — error `workflow_attribute not found in provider_args`.
- `workflow_attribute` present but empty — the provider returns nothing and the check fails with `Could not find input value`.
- A `workflow_attribute` name that is not in the table above is **not** an error: the provider returns an empty string `""`, which is then evaluated against the condition. Double-check spelling — a typo silently evaluates `""` instead of the intended value.

## Example

Verified end-to-end against the test fixtures:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/sg_workflow"
  },
  "evaluators": [
    {
      "id": "wf_check_1",
      "provider_args": {
        "operation_type": "attribute",
        "workflow_attribute": "useMarketplaceTemplate"
      },
      "condition": {
        "type": "Equals",
        "value": true
      }
    },
    {
      "id": "wf_check_2",
      "provider_args": {
        "operation_type": "attribute",
        "workflow_attribute": "integrationId"
      },
      "condition": {
        "type": "Contains",
        "value": "aws-qa"
      }
    },
    {
      "id": "wf_check_3",
      "provider_args": {
        "operation_type": "attribute",
        "workflow_attribute": "terraformVersion"
      },
      "condition": {
        "type": "RegexMatch",
        "value": "^1\\."
      }
    }
  ],
  "eval_expression": "wf_check_1 && wf_check_2 && wf_check_3"
}
```

Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md).
