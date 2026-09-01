# Add Tirith to a pipeline

Three pieces make a gate, and they are the same three on every platform:

1. a policy committed under `.tirith/policies/`,
2. the plan as JSON,
3. Tirith running with `--fail-on-error`.

Only the way you invoke it changes. Everything below is that pattern.

## Produce the input first

This is the step people leave out, and without it `plan.json` never exists:

```bash
terraform plan -out=tfplan -input=false     # or: tofu plan -out=tfplan -input=false
terraform show -json tfplan > plan.json     # or: tofu show -json tfplan > plan.json
```

Either binary works: they emit the same plan JSON and Tirith does not inspect which produced it.

**`-input=false` matters in CI.** Without it, a missing variable waits for a prompt nobody will
answer and the job hangs instead of failing. Locally you can leave it off.

## Install

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
```

Not PyPI: `pip install tirith` fetches an unrelated project. Pin the tag so a job cannot change
behaviour underneath you. Python 3.8 or newer, so any `python:3.x` image works.

Do **not** add `tirith lint` to a pipeline: it is not in the released package. See
`reference/validate.md`.

---

## GitHub Actions

Use the action. It finds the plan, posts a sticky pull-request comment, creates a check run and
sets the job's exit code.

```yaml
permissions:
  contents: read
  pull-requests: write   # the sticky comment
  checks: write          # the check run

steps:
  - uses: actions/checkout@v4

  - run: |
      terraform plan -out=tfplan -input=false
      terraform show -json tfplan > plan.json

  - uses: StackGuardian/tirith-iac-governance-action@v2
    with:
      fail-on-error: true
```

With `plan.json` in the working directory and policies under `.tirith/policies`, that is the whole
integration: no other `with:` keys are required, because the action finds the document by
convention (`plan.json` or `tfplan.json`). Without `fail-on-error` it reports findings but does
not block.

The two write permissions are the only setup the action cannot do for itself, and the usual cause
of a first install that runs but posts nothing.

## GitLab CI

No GitLab-native equivalent, so call the CLI directly, which is all the action does underneath.
Two jobs: one produces the artifact, the next gates on it.

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

If a plan job already exists, keep it: add `plan.json` to its `artifacts` and point the gate at it
with `needs`.

## Bitbucket Pipelines

Plan in one step, gate in the next, passing `plan.json` between them as an artifact.

```yaml
image: python:3.12

pipelines:
  pull-requests:
    '**':
      - step:
          name: Terraform plan
          script:
            - terraform plan -out=tfplan -input=false
            - terraform show -json tfplan > plan.json
          artifacts: [plan.json]
      - step:
          name: Policy gate
          script:
            - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
            - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

## Jenkins

Capture the exit code rather than letting `sh` fail, so `3` and `1` can be reported differently:

```groovy
stage('Policy gate') {
  steps {
    script {
      def code = sh(returnStatus: true, script: '''
        pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
        tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
      ''')
      if (code == 3)      { error('Tirith: a policy refused this change.') }
      else if (code != 0) { error("Tirith could not reach a verdict (exit ${code}).") }
    }
  }
}
```

## Azure DevOps

```yaml
- script: |
    terraform plan -out=tfplan -input=false
    terraform show -json tfplan > plan.json
  displayName: Terraform plan

- script: |
    pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
  displayName: Policy gate
```

`script` fails the task on any non-zero exit. To separate `3` from `1`, run the gate without
`--fail-on-error`, capture `$?`, and fail the task yourself.

## CircleCI

```yaml
jobs:
  policy-gate:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - attach_workspace: {at: .}
      - run: pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
      - run: tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

Persist `plan.json` to the workspace from the plan job.

## Any other runner

Anything that can run a container and produce a plan works the same way, including a cron job:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

Gate on the exit code, which every CI system already does.

---

## Make the exit code mean something

| Exit | What the job should do |
| --- | --- |
| `0` | Continue to `apply` |
| `3` | Fail the job: a policy refused the change |
| `1` | Fail the job, but report a **tool or input problem**, not a violation |

Collapsing `1` and `3` is the most common mistake in a Tirith pipeline. Exit `1` includes
`final_result: null`, which means every check was skipped and the policy evaluated nothing: a gate
that is not gating, reported as if the infrastructure were at fault.

## Keep the report

```bash
tirith --json -policy-path .tirith/policies -input-path plan.json > tirith-result.json
```

Publish it as a build artifact. It carries every evaluator, its result and the value that produced
it, which is what makes a failure explainable after the fact.

## Not yet available

A `tirith-lint` pre-commit hook and a VS Code task loop are in development, and both depend on
`tirith lint`, which is not in the released package. Do not write either into a pipeline today.
`https://stackguardian.github.io/tirith/roadmap/` tracks them.
