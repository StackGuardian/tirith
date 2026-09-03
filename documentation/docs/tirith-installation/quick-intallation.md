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
- Make sure your machine has [Python](https://www.python.org/downloads/) 3.8 or newer and [pip](https://pip.pypa.io/en/stable/installation/) installed.
- Install [Git](https://git-scm.com/downloads) on your machine.

## Steps to Install Tirith

### Step 1: Install using the `pip` command

:::danger Not from PyPI
`pip install tirith` installs an **unrelated project of the same name**, and `pip install py-tirith`
finds nothing: that is the package name in `setup.py` and it is not published. Installing Tirith
means installing from git, as below.
:::

Run the following command in your terminal to install Tirith directly from the GitHub repository,
pinned to a released tag:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
```

Pin the tag rather than tracking the default branch, so an install today and an install next month
give you the same tool. `1.2.0` is the newest tag;
`git ls-remote --tags https://github.com/StackGuardian/tirith.git` lists them all.

To use [the interactive interface](../tirith-usage/interactive-interface.md) as well, install the
optional extra, which needs Python 3.9 or newer:

```bash
pip install "py-tirith[tui] @ git+https://github.com/StackGuardian/tirith.git@1.2.0"
```

### Step 2: Verify Installation
Once installed, verify that Tirith is working by checking its version. You should see `1.2.0`,
which confirms both that the install succeeded and that you got the tag you asked for.
```bash
tirith --version
```
<br />
<img loading="lazy" src={require('../../assets/installation/tirith-version.png').default} alt="tirith-version" className="doc_img"/>