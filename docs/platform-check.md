# `tirith platform check`

Evaluate a terraform plan, state document or cost breakdown against the policies your StackGuardian
organization enforces, from any CI system or from a laptop.

The [GitHub Action](https://github.com/StackGuardian/tirith-iac-governance-action) is a thin wrapper
around this command. Use the action on GitHub; use this directly anywhere else — GitLab CI, a
Makefile, a local shell.

## What it does

1. **Masks the document on your machine**, before anything is uploaded. Values terraform marked
   sensitive are replaced with `__SG_REDACTED__`, root `variables` are dropped, and `prior_state` is
   removed. `json` and `kubernetes` documents are *not* masked — there is no schema that says which
   fields are secret.
2. **Packs** the masked documents with your terraform source into a `tar.gz`, excluding `.git`,
   `.terraform`, `*.tfstate*` and anything matched by `.gitignore`. `--source-dir ""` sends documents
   only. An oversized tree degrades to documents-only rather than failing.
3. **Uploads it** to the workflow's artifact directory and creates a StackGuardian workflow run.
4. **Polls** the run and prints the verdict, optionally as JSON and markdown for a later CI step.

Committed source ships as written: a secret hardcoded in HCL reaches the platform even though the
plan was masked. `--source-dir ""` is the opt-out.

## Credentials

`--api-key` / `$SG_API_TOKEN` and `--org` / `$SG_ORG`. The key should be an **organization** (`sgo_`)
token — `sgu_` keys are non-functional for SSO-group-only users, and are warned about rather than
rejected, so the symptom is a later 403.

`--api-key -` reads the key from stdin, which keeps it out of the process table and out of shell
history:

    echo "$SG_TOKEN" | tirith platform check --api-key - --workflow-id infra

## Workflow identity

`--workflow-id` names the StackGuardian workflow, and is created on first use. `--workflow-group`
defaults to `default`.

Two things worth knowing before choosing an id:

* Runs on one workflow **serialize** while another is pending. A matrix that shares an id becomes a
  queue, so give each leg its own.
* `--artifact-tag` namespaces the uploaded bundle. Two runs of the same workflow with the same tag
  and the same commit reuse one name, which is fine; different commits never collide.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Policies passed, or nothing was in scope |
| 1 | Could not complete the check |
| 2 | Timed out waiting for the run |
| 3 | A policy failed — only with `--fail-on-error` |
| 130 | Interrupted |

`3` exists so a caller can distinguish "your infrastructure violates a policy" from "Tirith could not
reach the platform". Without `--fail-on-error` a policy failure still exits `0`, and the verdict is
in `--output-json`.

## Full flag reference

```
usage: tirith platform check [-h] [--api-key API_KEY] [--org ORG]
                             [--region {eu,us}] [--api-url API_URL]
                             [--dashboard-url DASHBOARD_URL]
                             --workflow-id WORKFLOW_ID
                             [--workflow-group WORKFLOW_GROUP]
                             [--terraform-version TERRAFORM_VERSION]
                             [--repo-url REPO_URL] [--repo-ref REPO_REF]
                             [--step-template-id STEP_TEMPLATE_ID]
                             [--input-path INPUT_PATH] [--plan-file PLAN_FILE]
                             [--terraform-bin TERRAFORM_BIN]
                             [--input-kind {terraform_plan,terraform_state,kubernetes,json}]
                             [--state-path STATE_PATH]
                             [--infracost-path INFRACOST_PATH]
                             [--source-dir SOURCE_DIR] [--no-source]
                             [--sha SHA] [--artifact-tag ARTIFACT_TAG]
                             [--trigger-details-json TRIGGER_DETAILS_JSON]
                             [--trigger-details-file TRIGGER_DETAILS_FILE]
                             [--timeout TIMEOUT] [--output-json OUTPUT_JSON]
                             [--output-markdown OUTPUT_MARKDOWN]
                             [--comment-marker COMMENT_MARKER]
                             [--markdown-limit MARKDOWN_LIMIT]
                             [--fail-on-error]

Masks the document, packs it with the terraform source into an archive,
uploads it, runs the policies on StackGuardian and reports the verdict.

options:
  -h, --help            show this help message and exit

identity:
  --api-key API_KEY     API key, or '-' to read it from stdin. Default:
                        $SG_API_TOKEN
  --org ORG             Organization name. Default: $SG_ORG
  --region {eu,us}      StackGuardian region, setting both URLs at once.
                        Default: $SG_REGION or eu.
  --api-url API_URL     API base URL, with or without /api/v1. Overrides
                        --region; needed only for a self-hosted install or a
                        dedicated host. Default: $SG_BASE_URL
  --dashboard-url DASHBOARD_URL
                        Dashboard base URL, used to build run links. Inferred
                        from --api-url when it names a known region.

workflow:
  --workflow-id WORKFLOW_ID
                        Slug identifying the workflow. Created if absent.
                        Letters, digits, '-' and '_' only.
  --workflow-group WORKFLOW_GROUP
                        Workflow group. Created if absent.
  --terraform-version TERRAFORM_VERSION
                        Stored on the workflow at creation.
  --repo-url REPO_URL   Source repository URL, recorded on the workflow at
                        creation so it links back to the code.
  --repo-ref REPO_REF   Branch, tag or commit, recorded alongside --repo-url.
  --step-template-id STEP_TEMPLATE_ID
                        Override the policy-evaluation step template. Omit to
                        use the platform's own default.

inputs:
  --input-path INPUT_PATH
                        Document to evaluate. Defaults to whichever of
                        plan.json or tfplan.json is in --source-dir.
  --plan-file PLAN_FILE
                        Binary terraform plan. Rendered with `show -json` in
                        memory, so no unmasked plan JSON is written to disk.
  --terraform-bin TERRAFORM_BIN
                        terraform/tofu binary for --plan-file. Auto-detected,
                        preferring the real binary over a CI wrapper.
  --input-kind {terraform_plan,terraform_state,kubernetes,json}
  --state-path STATE_PATH
                        Optional terraform state, masked before upload.
  --infracost-path INFRACOST_PATH
                        Optional `infracost breakdown --format json`.
  --source-dir SOURCE_DIR
                        Terraform source to pack alongside the documents.
  --no-source           Send only the documents. Discovery still looks in --source-dir (or .) for the plan..

run:
  --sha SHA             Commit SHA, used to namespace the uploaded archive.
  --artifact-tag ARTIFACT_TAG
                        Namespaces the archive within a commit.
  --trigger-details-json TRIGGER_DETAILS_JSON
                        JSON object describing what triggered this run.
  --trigger-details-file TRIGGER_DETAILS_FILE
                        File containing that JSON object.
  --timeout TIMEOUT     Seconds to wait for the run. Default: 1800

output:
  --output-json OUTPUT_JSON
                        Write the result document here.
  --output-markdown OUTPUT_MARKDOWN
                        Write a markdown report here.
  --comment-marker COMMENT_MARKER
                        Opaque first line of the markdown, for stickiness.
  --markdown-limit MARKDOWN_LIMIT
                        Truncate the markdown to this length.
  --fail-on-error       Exit non-zero when a policy fails. An unreachable
                        platform or a run that produced no verdict always
                        exits non-zero regardless of this flag.
```
