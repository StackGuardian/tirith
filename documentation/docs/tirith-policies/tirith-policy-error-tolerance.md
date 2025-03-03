---
id: tirith-policy-error-tolerance
title: Error Tolerance
sidebar_label: Error Tolerance
description: This documentation overviews you about the introduction of the tirith software.
keywords:
  - tirith
  - stack-guardian
# url: https://www.lambdatest.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: tirith-policy-error-tolerance/
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
      "item": "https://www.lambdatest.com/support/docs/tirith-policy-error-tolerance/"
    }]
  })
}}></script>
Tirith supports error tolerance to handle missing or invalid keys in the input JSON.

## Handling Missing Keys

If a key referenced in an evaluator is missing, the evaluation typically fails. However, setting `error_tolerance` allows `evaluators` to be skipped instead of failing.

If we modify the previous policy to include `error_tolerance`, missing keys won’t cause a failure:
```javascript title="policy.json"
{
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
}
```

This ensures that if `verb` is missing, the evaluation is skipped rather than failing.