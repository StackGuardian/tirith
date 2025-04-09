---
id: tirith-policy-variables
title: Policy Variables
sidebar_label: Policy Variables
description: Understand how to use dynamic variables in Tirith policies for flexible policy definitions.
keywords:
  - tirith
site_name: Tirith
slug: tirith-policy-variables/
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Policy variables allow dynamic values in policy definitions. They can be referenced in conditions to make policies more flexible.

```json title="variables.json"
{
  "max_epoch": 1720415598
}
```

```json title="policy.json"
{
  "meta": {
    "version": "v1"
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "epoch_check",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "meta.epoch"
      },
      "condition": {
        "type": "LessThan",
        "value": "{{ max_epoch }}"
      }
    }
  ]
}
```

Example command:

```bash
tirith -input-path <INPUT_PATH> -policy-path policy.json -var-path variables.json
```

