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

Policy variables allow dynamic values in policy definitions. They can be referenced in conditions to make policies more flexible.

A variable is referenced as `{{ var.NAME }}`. The `var.` prefix is required — a placeholder written
without it, such as `{{ max_epoch }}`, is not recognised as a variable and is compared as the
literal string, so the check quietly measures the wrong thing instead of failing.

```json title="variables.json"
{
  "max_epoch": 1720415598
}
```

```json title="policy.json"
{
  "meta": {
    "version": "v1",
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
        "value": "{{ var.max_epoch }}"
      }
    }
  ],
  "eval_expression": "epoch_check"
}
```

Example command:

```bash
tirith -input-path <INPUT_PATH> -policy-path policy.json -var-path variables.json
```

Against an input of `{"meta": {"epoch": 1720000000}}` this passes:

```
Check: epoch_check
  PASSED
    1. PASSED: `1720000000` is less than `1720415598`
```

Supply variables inline with `-var` instead of, or in addition to, `-var-path`; an inline `-var`
wins when the same name is set in both. A variable that is referenced but never supplied is an
error, not an empty value: the run reports `Variables not found` and exits `1`.

See [Policy reference](tirith-policy-reference.md) for where `{{ var.NAME }}` may appear, and
[CLI reference](../tirith-usage/cli-reference.md) for the flags.

