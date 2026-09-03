# Evaluate against an organization's policies

`tirith platform check` evaluates against the policies a StackGuardian organization enforces,
instead of policy files committed to the repository — so policy lives in one place rather than
being copied into every repository that needs gating.

This is the **only** Tirith surface that talks to a network. Everything else runs locally.

## Minimum invocation

```bash
export SG_API_TOKEN=sgo_...   # an organization token
export SG_ORG=my-org

tirith platform check --workflow-id my-repo --input-path plan.json --fail-on-error
```

`--input-path` is optional when a `plan.json` or `tfplan.json` is in the working directory.

## What it does, in order

1. Masks Terraform-sensitive values **on your machine**, before anything leaves it.
2. Packs the masked documents with your Terraform source into an archive.
3. Uploads it, creates a run, polls it.
4. Prints the verdict, using the same exit codes as local evaluation.

## Flags worth knowing

| Flag | Use |
| --- | --- |
| `--region {eu,us}` | Which region. Default `eu`, or `$SG_REGION` |
| `--api-key -` | Read the key from stdin instead of the environment |
| `--plan-file tfplan` | A binary plan, rendered through `terraform show -json` in memory |
| `--input-kind` | `terraform_plan`, `terraform_state`, `kubernetes` or `json` |
| `--state-path` / `--infracost-path` | Add a state document or a cost breakdown to the run |
| `--no-source` | Send only the documents, not the Terraform source |
| `--timeout` | Seconds to wait for the run. Default `1800` |
| `--output-json` / `--output-markdown` | Write the verdict to files for a later CI step |
| `--api-url` | Overrides `--region` for a self-hosted or dedicated host |

## Exit codes

The same contract as local evaluation, plus one:

| Exit | Meaning |
| --- | --- |
| `0` | Passed |
| `1` | Could not reach a verdict — bad input, unreachable API |
| `2` | Timed out waiting for the run |
| `3` | A policy failed (with `--fail-on-error`) |

## Credentials

Never commit `SG_API_TOKEN`. In CI, supply it as a secret. `--api-key -` lets you pipe it in
without it appearing in a process list.

## When not to use it

If policies live in the repository and one team owns them, local evaluation is simpler, needs no
account, and sends nothing anywhere. Reach for `platform check` when the same policy has to apply
across many repositories and the results need to be visible in one place.
