---
id: tirith-policy-variables
title: Policy Variables
sidebar_label: Policy Variables
description: This documentation overviews you about the introduction of the tirith software.
keywords:
  - tirith
  - stack-guardian
# url: https://www.lambdatest.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: tirith-policy-variables/
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
      "item": "https://www.lambdatest.com/support/docs/tirith-policy-variables/"
    }]
  })
}}></script>
Policy variables allow dynamic values in policy definitions. They can be referenced in conditions to make policies more flexible.

```javascript title="policy.json"
{
  "meta": {
    "version": "v1",
    "variables": {
      "max_epoch": 1720415598
    }
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

This example allows `max_epoch` to be easily updated without modifying multiple evaluators.

