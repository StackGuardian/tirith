# Add Tirith to a pipeline

Three pieces make a gate: a policy committed to the repository, the plan as JSON, and Tirith
running with `--fail-on-error`.

## Produce the input first

```bash
tofu plan -out=tfplan -input=false          # or: terraform plan -out=tfplan -input=false
tofu show -json tfplan > plan.json          # or: terraform show -json tfplan > plan.json
```

Either binary works. They emit the same plan JSON, and Tirith does not inspect which one
produced it.

Everything below assumes `plan.json` exists.

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
  - run: terraform plan -out=tfplan -input=false
  - run: terraform show -json tfplan > plan.json
  - uses: StackGuardian/tirith-iac-governance-action@v2
    with:
      fail-on-error: true
```

With a `plan.json` in the working directory and policies under `.tirith/policies`, that is the
whole integration — no other `with:` keys are required. Without `fail-on-error` the action reports
findings but does not block the job.

## GitLab CI, or any container-based CI

There is no GitLab-native equivalent, so call the CLI directly — which is all the action does
underneath.

```yaml
policy:
  image: python:3.12
  needs: [plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.0.5"
    - tirith lint .tirith/policies
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

Nothing here is GitLab-specific. Any runner that can execute a container and produce a plan works
the same way.

## Bitbucket Pipelines

No native integration; call the CLI. Plan in one step, gate in the next, pass `plan.json` between
them as an artifact.

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
          artifacts: [plan.json, tfplan]
      - step:
          name: Policy gate
          script:
            - pip install "git+https://github.com/StackGuardian/tirith.git@1.0.5"
            - tirith lint .tirith/policies
            - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

## Jenkins

Declarative pipeline, gate as a stage. Capture the exit code rather than letting `sh` fail, so
`3` and `1` can be reported differently:

```groovy
stage('Policy gate') {
  steps {
    script {
      def code = sh(returnStatus: true,
        script: 'tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error')
      if (code == 3) { error('Tirith: a policy refused this change.') }
      else if (code != 0) { error("Tirith could not reach a verdict (exit ${code}).") }
    }
  }
}
```

## As a pre-commit hook

Tirith publishes a `tirith-lint` hook, so a broken policy is caught at commit time:

```yaml
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: 1.0.5
    hooks:
      - id: tirith-lint
```

It lints only; evaluating needs a plan, which means running `terraform plan` — too slow for a
commit hook and it would need cloud credentials. The hook triggers only when a file under
`.tirith/policies/` or a `*.tirith.json` changes, and lints the directory rather than the changed
files, because `tirith lint` takes a single path.

## In an editor, while writing

```bash
tirith lint .tirith/policies                                                  # shape
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error    # meaning
```

Wire those two as VS Code tasks (`.vscode/tasks.json`) with the second as the default test task,
and the whole loop is one keystroke. If you are drafting the policy for someone, run both before
handing it back, against a document that *should* fail — an exit code of `0` there means the
policy matched nothing.

## Make the exit code mean something

| Exit | What the job should do |
| --- | --- |
| `0` | Continue to `apply` |
| `3` | Fail the job — a policy refused the change |
| `1` | Fail the job, but report it as a **tool or input problem**, not a violation |

Collapsing `1` and `3` is the most common mistake: it reports an outage as a policy violation, and
a job that cannot tell them apart cannot tell a working gate from a broken one.

## Keep the report

```bash
tirith --json -policy-path .tirith/policies -input-path plan.json > tirith-result.json
```

Publish it as a build artifact. It carries the resource address, the planned action and the
before/after values for every finding, which is what makes a failure explainable after the fact.

## Order of operations

1. `tirith lint .tirith/policies` — catches a broken policy without touching infrastructure.
2. `terraform show -json` — produce the document.
3. `tirith … --fail-on-error` — the gate.

Lint first: it is the cheapest step and it fails on the class of mistake that would otherwise look
like a real violation.
