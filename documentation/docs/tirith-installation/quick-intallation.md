---
id: quick-installation
title: Quick Installation for Users
sidebar_label: Quick Setup
description: This documentation overviews you about the introduction of the Tirith software installation on your respective operating system.
keywords:
  - Tirith
  - StackGuardian
# url: https://www.tirith.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: quick-installation/
---

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
      "name": "Installation",
      "item": "https://www.lambdatest.com/support/docs/quick-installation/"
    }]
  })
}}></script>
If you simply want to install and start using Tirith, this option provides a fast installation process with minimal setup. Perfect for end users and non-developers who only need basic functionality.

## Prerequisite
- Make sure your machine has [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed.
- Install [Git](https://git-scm.com/downloads) on your machine.

## Steps to Install Tirith

### Step 1: Install using the `pip` command
Run the following command in your terminal to download Tirith directly from the GitHub repository and install it on your local system. This command ensures that you have the latest version.

```bash
pip install git+https://github.com/StackGuardian/tirith.git
```
    

### Step 2: Verify Installation
Once installed, verify that Tirith is working by checking its version. You should see a version number (e.g., 1.0.0-beta.12) indicating successful installation.
```bash
tirith --version
```
<br />
<img loading="lazy" src={require('../../assets/installation/tirith-version.png').default} alt="tirith-version" className="doc_img"/>