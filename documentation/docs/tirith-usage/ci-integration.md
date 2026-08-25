---
id: ci-integration
title: CI Integration
sidebar_label: CI Integration
description: Running Tirith in GitHub Actions via the action, and in GitLab CI or any container-based CI via the CLI directly.
keywords:
  - tirith
  - ci
  - github actions
  - gitlab
site_name: Tirith
slug: ci-integration/
---

Tirith reads the plan your pipeline already produces — the output of
`terraform show -json tfplan` — checks it against your policies, and exits non-zero so a violating
change never reaches `apply`. The same policy files gate a GitHub Actions job, a GitLab job and a
laptop.

Two ways to run it in CI:

- **GitHub Actions** — use the
  [StackGuardian/tirith-iac-governance-action](https://github.com/StackGuardian/tirith-iac-governance-action),
  which wraps the CLI and adds the GitHub-specific reporting.
- **Everything else** — GitLab CI, or any CI that can run a container — invoke the CLI directly,
  which is all the action does underneath.

Either way, the job is gated by the [exit code](exit-codes.md): pass `--fail-on-error` (or the
action's `fail-on-error` input) and a failing policy fails the job.

## GitHub Actions

The action finds the plan, evaluates the policies, posts a sticky pull-request comment, creates a
check run and sets the job's exit code:

```yaml
permissions:
  contents: read
  pull-requests: write   # sticky comment
  checks: write          # check run

steps:
  - run: |
      terraform plan -out=tfplan -input=false
      terraform show -json tfplan > plan.json

  - uses: StackGuardian/tirith-iac-governance-action@v2
```

With a `plan.json` in the working directory that is the whole integration — no `with:` block. The
action finds the document by convention (`plan.json` or `tfplan.json`) and evaluates the policy
files committed under `.tirith/policies`, on the runner, talking to nothing. Add
`with: { fail-on-error: true }` to make a failing policy fail the job.

### Local mode and platform mode

The action has two modes, chosen by whether credentials are present — there is no switch:

- **Without credentials** (the default), policy files from your repository are evaluated on the
  runner. Nothing is uploaded and no account is needed.
- **With credentials**, the action evaluates the policies your StackGuardian organization enforces
  instead, by way of `tirith platform check` — see [Platform Check](platform-check.md):

```yaml
env:
  SG_API_TOKEN: ${{ secrets.SG_API_TOKEN }}
  SG_ORG: ${{ vars.SG_ORG }}
```

Everything on the pull request is the same in both modes — the same comment, the same
`Tirith IaC Governance` check run, the same outputs and exit codes.

### Commonly used inputs

Every input is optional. The full list, with the matrix/monorepo guidance and the outputs, is in
the [action's own README](https://github.com/StackGuardian/tirith-iac-governance-action#readme).

| Input | Default | |
|---|---|---|
| `policy-path` | `.tirith/policies` | Local mode only: a file, directory or glob of policy files |
| `input-path` | `plan.json` / `tfplan.json` | Document to evaluate, found by convention |
| `plan-file` | | Binary plan, rendered with `terraform show -json` in memory |
| `input-kind` | `terraform_plan` | `terraform_plan`, `terraform_state`, `kubernetes`, `json` |
| `fail-on-error` | `false` | Fail the job when a policy fails |
| `sg-region` | `eu` | `eu` or `us`; platform mode only |
| `source-dir` | `.` | Platform mode: the terraform source uploaded with the documents; `""` sends documents only |
| `timeout` | `1800` | Platform mode: seconds to wait for the run |

The action's exit behaviour follows the shared contract: `fail-on-error` governs policy verdicts,
while a run that errored, an unreachable platform, or a job with no credentials *and* no policies
is always red — a check that gated nothing must not report green.

### Outputs

The action exposes `verdict` (`passed` | `warned` | `failed` | `errored` | `no-policies`), `mode`
(`platform` | `local`), the `passed` / `failed` / `warned` counts, the full result document as
`results` and `results-file`, and — in platform mode — `wfrun-id` and `wfrun-url` linking to the
run.

## GitLab CI

There is no GitLab-native equivalent of the action, so you invoke the CLI directly. Given an
earlier job that saved `plan.json` as an artifact:

```yaml
policy:
  image: python:3.12
  needs: [plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

Tirith is **not on PyPI** — `pip install tirith` installs an unrelated project of the same name.
Install from git, and pin a tag rather than tracking the default branch so a CI job cannot change
behaviour underneath you. `1.2.0` is the newest tag;
`git ls-remote --tags https://github.com/StackGuardian/tirith.git` lists them. Python 3.8 or newer.

To evaluate your organization's policies instead of the committed files, swap the last line for
`tirith platform check` and supply credentials as CI variables:

```yaml
policy:
  image: python:3.12
  needs: [plan]
  variables:
    SG_ORG: my-org       # SG_API_TOKEN comes from a masked CI/CD variable
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    - tirith platform check --workflow-id my-repo --input-path plan.json --fail-on-error
```

See [Platform Check](platform-check.md) for what that uploads and what it masks first.

## Any container-based CI

Nothing above is GitLab-specific: any runner that can execute a container and produce a plan works
the same way. The recipe is always the same three steps —

1. produce the input document (`terraform show -json tfplan > plan.json`);
2. `pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"`;
3. `tirith -policy-path <policies> -input-path plan.json --fail-on-error`

— and gate the job on the exit code, which every CI system does by default for a non-zero exit.
Use `--json` to capture the result document for a later step, and see [Exit codes](exit-codes.md)
for telling a policy failure (`3`) apart from a tooling failure (`1`).
