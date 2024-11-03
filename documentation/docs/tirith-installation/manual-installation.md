---
id: manual-installation
title: Manual Installation (Using a Python Virtual Environment)
sidebar_label: Manual Setup
description: This documentation overviews you about the introduction of the Tirith software installation on your respective operating system.
keywords:
  - Tirith
  - StackGuardian
# url: https://www.tirith.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: manual-installation/
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
      "item": "https://www.lambdatest.com/support/docs/manual-installation/"
    }]
  })
}}></script>
If you prefer a manual setup, especially if you want to modify Tirith’s codebase directly, follow these steps to install Tirith in a virtual Python environment.

## Prerequisite
- Make sure your machine has [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed.
- Install [Git](https://git-scm.com/downloads) on your machine.

## Steps to Install Tirith

### Step 1: Clone the Repository
Clone the Tirith repository from GitHub to get the latest code:

```bash
git clone https://github.com/StackGuardian/tirith.git
cd tirith
```

### Step 2: Set Up a Python Virtual Environment
Setting up a virtual environment isolates Tirith’s dependencies, preventing potential conflicts with other projects on your machine.

Create a Virtual Environment:

```bash
virtualenv .venv
```

Activate the Virtual Environment:

```bash
source .venv/bin/activate
```

This command activates the virtual environment, ensuring all packages you install are contained within this environment.

### Step 3: Install Tirith
With the virtual environment activated, install Tirith:

```bash
pip install -e .
```
The -e flag installs Tirith in `editable` mode, allowing you to make modifications to the codebase without needing to reinstall the package.

### Step 4: Verify Installation
To confirm Tirith is installed and running properly, check its version:

```bash
tirith --version
```
You should see a version number output, verifying that Tirith is set up correctly.
<br />
<img loading="lazy" src={require('../../assets/installation/tirith-version.png').default} alt="tirith-version" className="doc_img"/>