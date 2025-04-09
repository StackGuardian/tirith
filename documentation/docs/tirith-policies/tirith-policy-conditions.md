---
id: tirith-policy-conditions
title: Policy Conditions
sidebar_label: Policy Conditions
description: Discover the various condition types supported by Tirith for evaluating input JSON.
keywords:
  - tirith
site_name: Tirith
slug: tirith-policy-conditions/
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Conditions define how values from input JSON are evaluated. Tirith supports various condition types:

- **Equals :** Checks if a value matches a specified value.
- **RegexMatch :** Validates if a string matches a regex pattern.
- **LessThan / GreaterThan :** Compares numeric values.

```jsonc title="policy.json"
{
  // ...
  "id": "epoch_check",
  "provider_args": {
    "operation_type": "get_value",
    "key_path": "meta.epoch"
  },
  "condition": {
    "type": "LessThan",
    "value": 1720415598
  }
  // ...
}
```

This condition ensures that the `meta.epoch` value is less than `1720415598`.
