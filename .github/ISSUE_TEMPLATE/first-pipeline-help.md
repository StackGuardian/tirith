---
name: Help me govern my first IaC pipeline
about: Get help adding a local, credential-free first check to your pipeline
title: 'Help: first pipeline — '
labels: ['help wanted', 'first-pipeline']
assignees: ''
---

A Tirith maintainer or community member can help you add a local,
credential-free first check.

**Do not include secrets, plan files or private source code in this issue.**
Redact anything you paste, or reduce it to a minimal public example.

### CI system

<!-- GitHub Actions / GitLab CI / other (which?) -->

### IaC tool and version

<!-- Terraform or OpenTofu, and the version -->

### How the plan is produced, and where the plan JSON ends up

<!-- e.g. "terraform plan -out=tfplan in a plan job, artifact passed to the next job" -->

### The first guardrail you want to enforce

<!-- In plain words is fine: "every S3 bucket must have an Owner tag", "no
     destroy of anything tagged production" -->

### A public example repository, or a redacted workflow snippet

<!-- Optional, but it is the difference between a general answer and a specific one -->
