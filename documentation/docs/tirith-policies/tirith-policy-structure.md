---
id: tirith-policy-structure
title: Policy Structure
sidebar_label: Policy Structure
description: This documentation overviews you about the introduction of the tirith software.
keywords:
  - tirith
  - stack-guardian
# url: https://www.lambdatest.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: tirith-policy-structure/
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
      "item": "https://www.lambdatest.com/support/docs/tirith-policy-structure/"
    }]
  })
}}></script>
Tirith policies are written in JSON format, following a structured approach that defines rules and conditions for evaluating input data. Each policy consists of:

- **Metadata** (`meta`): Specifies the policy version and required provider.
- **Evaluators** (`evaluators`): A list of conditions that determine if the input meets the policy requirements.
- **Evaluation Expression** (`eval_expression`): Defines how evaluators are combined to determine the final result.

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
    }
  ],
  "eval_expression": "can_post"
}
```