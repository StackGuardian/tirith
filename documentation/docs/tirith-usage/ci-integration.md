---
id: ci-integration
title: CI Integration
sidebar_label: CI Integration
description: Running Tirith in GitHub Actions, GitLab CI, Bitbucket Pipelines, Jenkins, or any container-based CI, plus a pre-commit hook.
keywords:
  - tirith
  - ci
  - github actions
  - gitlab
  - bitbucket
  - jenkins
  - pre-commit
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
  - run: terraform plan -out=tfplan -input=false

  - uses: StackGuardian/tirith-iac-governance-action@v2
    with:
      plan-file: tfplan
      fail-on-error: true
```

The two write permissions are the only setup the action cannot do for itself, and are the thing
most often missing on a first install. `-input=false` matters in CI: without it a missing variable
waits for a prompt that never comes, and the job hangs instead of failing.

Handing the action the **binary plan** rather than exporting JSON first is one step shorter and
strictly safer: the action renders it with `terraform show -json` in memory, so no unmasked plan
JSON is written to the workspace where a later step, a cache or an artifact upload could pick it
up.

If your pipeline already writes `plan.json`, drop `plan-file` and the action finds the document by
convention (`plan.json` or `tfplan.json`). Either way it evaluates the policy files committed under
`.tirith/policies`, on the runner, talking to nothing.

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

There is no GitLab-native equivalent of the action, so you invoke the CLI directly. Two jobs: one
produces the plan as an artifact, the next gates on it.

```yaml
plan:
  stage: plan
  script:
    - terraform plan -out=tfplan -input=false
    - terraform show -json tfplan > plan.json
  artifacts:
    paths: [plan.json]

policy:
  stage: test
  image: python:3.12
  needs: [plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

If you already have a plan job, keep it — add `plan.json` to its `artifacts` and point the gate at
it with `needs`. `-input=false` matters in CI: without it a missing variable waits for a prompt that
will never come, and the job hangs instead of failing.

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

## Bitbucket Pipelines

Bitbucket has no Tirith-native integration, so the CLI is called directly — which is all the
GitHub Action does underneath. Plan in one step, gate in the next, and pass the plan between them
as an artifact.

```yaml title="bitbucket-pipelines.yml"
image: python:3.12

pipelines:
  pull-requests:
    '**':
      - step:
          name: Terraform plan
          script:
            - terraform plan -out=tfplan -input=false
            - terraform show -json tfplan > plan.json
          artifacts: [plan.json, tfplan]
      - step:
          name: Policy gate
          script:
            - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
            - tirith lint .tirith/policies   # needs a build from main until the next release
            - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

A worked repository is at
[tirith-bitbucket-demo](https://bitbucket.org/__refeed__/tirith-bitbucket-demo).

## Jenkins

A declarative pipeline with the gate as a stage between plan and apply. The one thing worth doing
deliberately is keeping exit `3` and exit `1` apart, so a tooling problem is not reported as a
policy violation:

```groovy title="Jenkinsfile"
stage('Policy gate') {
  steps {
    script {
      def code = sh(
        returnStatus: true,
        script: 'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error',
      )
      if (code == 3) {
        error('Tirith: a policy refused this change.')
      } else if (code != 0) {
        error("Tirith could not reach a verdict (exit ${code}).")
      }
    }
  }
}
```

`returnStatus: true` is what makes this work: without it the shell step throws on any non-zero
exit and the two cases become one.

## As a pre-commit hook

:::warning In development
`tirith lint` is not in 1.2.0 and the `tirith-lint` hook id is not published, so the
configuration below does not work yet: `pre-commit` cannot resolve the hook and the run fails.
It is documented here because the design is settled and the shape will not change. Track it on
the [roadmap](https://stackguardian.github.io/tirith/roadmap/).
:::

Catch a broken policy before it is committed, let alone before CI runs it. Tirith will publish a
`tirith-lint` hook:

```yaml title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: main          # 1.2.0 predates the hook; pin the first tag that includes it
    hooks:
      - id: tirith-lint
      - id: tirith-fmt
```

```bash
pre-commit install
pre-commit run tirith-lint --all-files
```

The hooks run only when a file under `.tirith/` or a `*.tirith.json` changes, and lint exactly the
files that changed. `tirith-fmt` rewrites them into the canonical layout; commit again after it
does.

:::note Why linting and not evaluation
Evaluating a policy needs a plan document, and producing one means running `terraform plan` —
too slow for a commit hook, and it needs cloud credentials a hook has no business holding.
Linting is pure local computation over JSON: fast, offline, and it catches the class of mistake
that otherwise reaches CI looking like a real infrastructure violation.
:::

## Worked repositories

Each of these is a small, real IaC pipeline with Tirith in front of it:

| Platform | Repository |
| --- | --- |
| GitHub Actions | [StackGuardian/tirith-action-demo](https://github.com/StackGuardian/tirith-action-demo) |
| GitLab CI | [stackguardian/tirith-component-demo](https://gitlab.com/stackguardian/tirith-component-demo) |
| Bitbucket Pipelines | [__refeed__/tirith-bitbucket-demo](https://bitbucket.org/__refeed__/tirith-bitbucket-demo) |

They follow the same five chapters: check the plan against policies in the repository, take the
policies from the organization instead, add a resource that violates one, fix it, and publish the
state after apply.
