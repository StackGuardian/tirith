---
id: tirith-create-first-policy
title: Creating Your First Tirith Policy
sidebar_label: Policy
description: This documentation overviews you about the introduction of the tirith software.
keywords:
  - tirith
  - stack-guardian
# url: https://www.lambdatest.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: tirith-create-first-policy/
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<script type="application/ld+json"
  dangerouslySetInnerHTML={{ __html: JSON.stringify({
   "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [{
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://www.lambdatest.com"
    },{
      "@type": "ListItem",
      "position": 2,
      "name": "Support",
      "item": "https://www.lambdatest.com/support/docs/"
    },{
      "@type": "ListItem",
      "position": 3,
      "name": "Tirith Policies",
      "item": "https://www.lambdatest.com/support/docs/tirith-create-first-policy/"
    }]
  })
}}></script>
In modern cloud-native environments, security and compliance are paramount. Tirith, a powerful policy-as-code framework by StackGuardian, enables you to enforce robust validation and guardrails over JSON-based inputs. By defining policies in JSON format, you can automate security and operational controls efficiently within your cloud and DevOps workflows.

This guide provides a hands-on approach to creating and evaluating a Tirith policy against a JSON input file. You will learn how to:

- Use the Tirith CLI to validate policies against JSON inputs
- Leverage the Tirith JSON provider for extracting and validating data

## Prerequisites

Before starting, ensure you have the Tirith CLI installed and create the following two JSON files: `input.json` and `policy.json`:

```javascript title="input.json"
{
  "path": "/stackguardian/wfgrps/test",
  "verb": "POST",
  "meta": {
    "epoch": 1718860398,
    "User-Agent": {
        "name": "User-Agent",
        "value": "PostmanRuntime/7.26.8"
    }
  }
}
```

Here is the `policy.json` file:

```javascript title="policy.json"
{
    "meta": {
        "version": "v1",
        "required_provider": "stackguardian/json"
    },
    "evaluators": [
        {
            "id": "can_post",
            "provider_args": {
                "operation_type": "get_value",
                "key_path": "verb"
            },
            "condition": {
                "type": "Equals",
                "value": "POST"
            }
        },
        {
            "id": "wfgrps_path",
            "provider_args": {
                "operation_type": "get_value",
                "key_path": "path"
            },
            "condition": {
                "type": "RegexMatch",
                "value": "/stackguardian/wfgrps/test.*"
            }
        },
        {
            "id": "epoch_less_than_8th_july_2024",
            "provider_args": {
                "operation_type": "get_value",
                "key_path": "meta.epoch"
            },
            "condition": {
                "type": "LessThan",
                "value": 1720415598
            }
        }
    ],
    "eval_expression": "can_post && wfgrps_path && epoch_less_than_8th_july_2024"
}
```

## Evaluating the Policy Against the Input

Once you have created the input and policy files, execute the following command to evaluate the policy:

```bash
tirith -input-path input.json -policy-path policy.json
```

Explanation:

- `tirith`: The core command to run the Tirith policy evaluation engine.
- `-input-path input.json`: Specifies the JSON input file containing data to be validated.
- `-policy-path policy.json`: Points to the JSON policy file defining validation rules.

```bash
Check: can_post
  PASSED
  Results:
	1. PASSED: POST is equal to POST

Check: wfgrps_path
  PASSED
  Results:
	1. PASSED: /stackguardian/wfgrps/test matches regex pattern /stackguardian/wfgrps/test.*

Check: epoch_less_than_8th_july_2024
  PASSED
  Results:
	1. PASSED: 1718860398 is less than 1720415598

Passed: 3 Failed: 0 Skipped: 0

Final expression used:
-> can_post && wfgrps_path && epoch_less_than_8th_july_2024
✔ Passed final eval
```

This confirms that the input successfully meets all defined policy conditions.

By implementing policies in Tirith, you can ensure consistent enforcement of security, compliance, and operational rules across your cloud and DevOps pipelines. In the next sections, we will explore more advanced features such as policy conditions, variables, and error tolerance handling to make your policies more dynamic and resilient.