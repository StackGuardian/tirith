---
id: developer-mode-installation
title: Installation for Developers (Using Docker and Dev Containers in VS Code)
sidebar_label: Developer Mode Setup
description: This documentation overviews you about the introduction of the Tirith software installation on your respective operating system.
keywords:
  - Tirith
  - StackGuardian
# url: https://www.tirith.com/support/docs/getting-started-with-tirith
site_name: Tirith
slug: developer-mode-installation/
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
      "item": "https://www.lambdatest.com/support/docs/developer-mode-installation/"
    }]
  })
}}></script>
For developers who want to contribute to Tirith, setting up a [Dev Container in Visual Studio Code (VS Code)](https://code.visualstudio.com/docs/devcontainers/create-dev-container#_create-a-devcontainerjson-file) offers a robust development environment. This approach ensures that all dependencies and configurations are consistent across different setups.

## Prerequisite

- Ensure [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) are installed on your machine.
- Install [Git](https://git-scm.com/downloads) in your machine.
- Basic knowledge on [Docker](https://docs.docker.com/engine/install/) is required.

## Steps to Install Tirith

### Step 1: Clone the Repository
Clone the Tirith repository from GitHub to get the latest code:

```bash
git clone https://github.com/StackGuardian/tirith.git
cd tirith
```

### Step 2: Set Up Docker
Ensure [Docker](https://docs.docker.com/engine/install/) is installed and running on your machine. You can manage Docker using Docker Desktop or the command line interface (CLI). Docker allows you to run Tirith within isolated containers, preventing any dependency conflicts with your local system.

### Step 3: Open the Project in VS Code
- Launch Visual Studio Code and open the cloned repository folder.
- Open the Command Palette by pressing `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS).
- Search for **Dev Containers: Rebuild and Reopen in Container** and select this option.
- VS Code will use the `devcontainer.json` configuration file within the project to build a containerized environment for Tirith. This configuration file contains settings for the development environment, such as necessary extensions and dependencies. Building the container may take a few minutes.
- Once the container is running, you’ll have a fully configured development environment within Docker, optimized for Tirith development.