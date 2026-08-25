# Repository metadata

GitHub's About panel, topics and social preview cannot be set from a file in
the repository — a maintainer has to apply them in **Settings** and in the
sidebar's **About** gear. This file is the source of truth for what they should
say, so the values are reviewable in a pull request rather than living only in
one person's browser.

Keep it in step with the landing page (`documentation/src/pages/index.js`) and
the README opening.

## About

**Description**

> Open-source IaC governance for any Terraform or OpenTofu pipeline. Evaluate
> plans locally, explain failures and stop unsafe changes before apply.

**Website**

> https://stackguardian.github.io/tirith/

**Topics**

```
terraform
opentofu
infrastructure-as-code
policy-as-code
devops
platform-engineering
ci-cd
compliance
cloud-security
github-actions
gitlab-ci
```

## Social preview

Settings → General → Social preview. 1280×640.

**Title**

> Tirith — open-source IaC governance

**Subtitle**

> Put governance in front of every Terraform or OpenTofu plan.

> [!NOTE]
> **Open item:** the image itself does not exist yet. Until it is uploaded,
> GitHub falls back to the repository owner's avatar, which reads as a
> StackGuardian link rather than a project link.

## Settings to confirm before launch

- **Private vulnerability reporting** enabled (Settings → Security). Without
  it, the reporting link in [SECURITY.md](../SECURITY.md) does not work.
- **Discussions** enabled, if the "tell us how the first plan went" link on the
  landing page is to resolve; otherwise repoint it at Issues.
- A **`good first issue`** label with 8–12 genuinely scoped issues behind it.
  Both the README and the landing page link to that label.
- **`POSTHOG_KEY`** repository secret and optional **`POSTHOG_HOST`** variable,
  read by `.github/workflows/deploy_docs.yml`. Unset means the published site
  ships no analytics, which is a safe default rather than a failure.
- **`HUBSPOT_PORTAL_ID`** and **`HUBSPOT_FORM_GUID`** repository variables, for
  the Fleet enquiry form. The HubSpot form needs properties named `email`,
  `company`, `repository_band`, `ci_systems`, `primary_problem` and `context`.
  Unset, the form disables itself and points at GitHub Issues instead.

## Naming

Search results and social cards use **Tirith IaC Governance** (the Docusaurus
site title) rather than bare "Tirith", to distinguish the project from the
unrelated Tirith terminal-security tool and the unrelated `tirith` package on
PyPI. Keep that qualifier in any new SEO-facing copy.
