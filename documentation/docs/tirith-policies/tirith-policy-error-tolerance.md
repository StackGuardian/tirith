---
id: tirith-policy-error-tolerance
title: Error Tolerance
sidebar_label: Error Tolerance
description: Learn how Tirith handles missing or invalid keys in policies using error tolerance.
keywords:
  - tirith
site_name: Tirith
slug: tirith-policy-error-tolerance/
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Tirith supports error tolerance to handle missing or invalid keys in the input JSON.

## Handling Missing Keys

If a key referenced in an evaluator is missing, the evaluation typically fails. However, setting `error_tolerance` allows `evaluators` to be skipped instead of failing.

If we modify the previous policy to include `error_tolerance`, missing keys won’t cause a failure:
```jsonc title="policy.json"
{
  // ...
  "id": "can_post",
  "provider_args": {
    "operation_type": "get_value",
    "key_path": "verb"
  },
  "condition": {
    "type": "Equals",
    "value": "POST",
    "error_tolerance": 2
  }
  // ...
}
```

This ensures that if `verb` is missing, the evaluation is skipped rather than failing.
