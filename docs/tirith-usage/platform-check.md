# Platform Check

Source: https://stackguardian.github.io/tirith/docs/tirith-usage/platform-check/
Summary: The tirith platform check subcommand — every flag, what it uploads, what it masks on your machine first, and what it reports back.

`tirith platform check` evaluates a terraform plan, state document or cost breakdown against the
policies your **StackGuardian organization** enforces, from any CI system or from a laptop —
instead of policy files committed to your repository. Policy then lives in one place rather than
being copied into every repository that needs gating.

This is the one part of Tirith that talks to a network and needs an account. Plain
`tirith` — local evaluation — needs neither; see the [CLI reference](cli-reference.md).

```sh
export SG_API_TOKEN=sgo_...        # an organization token
export SG_ORG=my-org

tirith platform check --workflow-id my-repo --input-path plan.json --fail-on-error
```

`--input-path` is optional when a `plan.json` or `tfplan.json` is in the working directory.

On GitHub, prefer the
[GitHub Action](https://github.com/StackGuardian/tirith-iac-governance-action), which is a thin
wrapper around this command and adds the pull-request comment and check run — see
[CI integration](ci-integration.md). Use this command directly anywhere else: GitLab CI, a
Makefile, a local shell.

## What it does

1. **Masks the document on your machine**, before anything is uploaded (details below).
2. **Packs** the masked documents together with your terraform source into a `tar.gz`, excluding
   `.git`, `.terraform`, `*.tfstate*` and anything matched by `.gitignore`. `--no-source` sends
   documents only. An oversized source tree degrades to documents-only with a warning rather than
   failing the check.
3. **Uploads** the archive to the workflow's artifact directory and creates a StackGuardian
   workflow run. The workflow and its group are created on first use.
4. **Polls** the run until it finishes and prints the verdict — optionally also as JSON and
   markdown files for a later CI step.

## What it masks

Masking happens client-side, on your machine, before anything leaves it. Masked values are
replaced with the sentinel `__SG_REDACTED__`.

For a **terraform plan** (`--input-kind terraform_plan`, the default):

- Every value terraform marked sensitive (`before_sensitive` / `after_sensitive`) is masked, in
  `resource_changes`, `resource_drift` and `output_changes` alike.
- Root `variables` are dropped wholesale — the plan does not reliably mark which were declared
  `sensitive`, so the only safe assumption is that all of them might be.
- `prior_state` is dropped, and terraform's own `planned_values` — which mirrors every value with
  no sensitivity markers — is dropped and **rebuilt from the already-masked** `resource_changes`,
  so tools that read that section still work without the leak.
- Credential-bearing literals in `configuration` (provider blocks, resource expressions, module
  arguments, variable defaults) are scrubbed while the reference graph policies read is kept.
- Finally, any string terraform marked sensitive *somewhere* is masked *everywhere* in the
  document — catching provider-computed mirrors such as `tags_all` that carry the same plaintext
  without a marker of their own.

For a **terraform state document** (`--input-kind terraform_state`, or `--state-path`): outputs
marked `sensitive` and every attribute named in an instance's `sensitive_attributes` are masked,
and the same everywhere-sweep is applied. Both shapes are handled — raw `terraform state pull`
output and `terraform show -json` output.

Two limits, stated plainly:

- **`json` and `kubernetes` documents are not masked** — there is no schema that says which fields
  are secret. A document that looks like terraform state but is sent with the wrong `--input-kind`
  triggers a warning, because that is the mistake that would ship every attribute in plaintext.
- **Committed source ships as written.** Masking applies to the documents, not to your repository:
  a secret hardcoded in a `.tf` file reaches the platform even though the plan was masked.
  `--no-source` is the opt-out. Terraform's `*_sensitive` markers are also not exhaustive — a
  value that flows through `locals`, or comes from a provider that did not mark its schema, is not
  caught by marker-driven masking.

The number of masked values is printed before upload, and recorded in the bundle's metadata.

## What it uploads

One `tar.gz` archive per run, in the workflow's artifact directory, with a fixed layout:

```
plan.json          the masked terraform plan
tfstate.json       the masked state, if one was supplied
infracost.json     the cost breakdown, if one was supplied
metadata.json      what this bundle is: origin, repository, commit, masking, workflow identity
code/              the terraform source, if any was packed
```

The archive is retained after the run — it is the source that produced the findings, and other
systems read it to see the code a verdict came from. When a state document is supplied, the masked
copy is additionally published as the workflow's `tfstate.json` artifact so it appears in the
platform's State view; that copy is masked and cannot be used to run terraform. The full
`metadata.json` field reference is in
[docs/platform-check.md](https://github.com/StackGuardian/tirith/blob/main/docs/platform-check.md)
in the repository.

## What it reports back

- **Progress and the verdict headline go to stderr**, so stdout stays clean for machine-readable
  output: the masking count, the upload, a link to the created run, each poll of the run's status,
  and finally a one-line headline such as `Tirith — 3 failed, 1 warned`.
- **`--output-json`** writes the result document: the run `status`, the `verdict`
  (`passed` | `warned` | `failed` | `no-policies` | `errored`), per-outcome `counts` (passed,
  failed, warned, approval_required, skipped, unknown), the `headline`, `wfrun_id` and `wfrun_url`
  linking to the run, the full `policy_results`, the `monthly_cost` when a cost breakdown was
  evaluated, and where the uploaded archive lives (`archive_key`, `source_packed`,
  `source_skipped_reason`). It is written once with `status: RUNNING` as soon as the run is
  created — so a timeout still leaves the run discoverable — and again with the final result.
- **`--output-markdown`** writes a rendered report, suitable for posting as a pull-request or
  merge-request comment by a later CI step. `--comment-marker` sets an opaque first line so your
  script can find and update its own previous comment, and `--markdown-limit` truncates the body
  (default 60000 characters).
- **The exit code** follows the shared [contract](exit-codes.md): `0` passed, `1` the check could
  not be completed, `3` a policy failed (only with `--fail-on-error`), `130` interrupted. A run
  that produced no verdict — errored, unreachable, unreadable results — always exits non-zero
  regardless of `--fail-on-error`: it fails closed. A policy that asks for approval is reported as
  a warning and does not block, because the evaluation has already finished by the time the intent
  is known.

## Credentials

`--api-key` / `$SG_API_TOKEN` and `--org` / `$SG_ORG` are required. The key should be an
**organization** (`sgo_`) token — `sgu_` user tokens are non-functional for SSO-group-only users
and are warned about rather than rejected, so the symptom is a later 403.

`--api-key -` reads the key from stdin, which keeps it out of the process table and out of shell
history:

```sh
echo "$SG_TOKEN" | tirith platform check --api-key - --workflow-id infra
```

## Flag reference

### Identity

| Flag | Default | What it does |
|---|---|---|
| `--api-key` | `$SG_API_TOKEN` | API key, or `-` to read it from stdin |
| `--org` | `$SG_ORG` | Organization name |
| `--region` | `$SG_REGION` or `eu` | StackGuardian region, `eu` or `us`. Sets both the API and dashboard URLs at once |
| `--api-url` | `$SG_BASE_URL` | API base URL, with or without `/api/v1`. Overrides `--region`; needed only for a self-hosted install or a dedicated host |
| `--dashboard-url` | `$SG_DASHBOARD_URL` | Dashboard base URL, used to build run links. Inferred from `--api-url` when it names a known region |

`--region` and an explicit URL cannot be combined — they set the same thing, and silently picking
one would hide the contradiction.

### Workflow

| Flag | Default | What it does |
|---|---|---|
| `--workflow-id` | *(required)* | Slug identifying the StackGuardian workflow. Created if absent. Letters, digits, `-` and `_` only; anything else is rejected with a suggested slug |
| `--workflow-group` | `default` | Workflow group. Created if absent — note that policies are scoped per group, so a typo silently enforces nothing |
| `--terraform-version` | | Stored on the workflow at creation |
| `--repo-url` | | Source repository URL, recorded on the workflow at creation so it links back to the code. Any credential embedded in the URL is stripped before it is recorded |
| `--repo-ref` | | Branch, tag or commit, recorded alongside `--repo-url` |
| `--repo-path` | inferred | Path of `--source-dir` within the repository, recorded in the bundle's `metadata.json`. Inferred from the enclosing git checkout if omitted |
| `--step-template-id` | platform default | Override the policy-evaluation step template |

Runs on one workflow serialize while another is pending — a matrix that shares an id becomes a
queue, so give each leg its own.

### Inputs

| Flag | Default | What it does |
|---|---|---|
| `--input-path` | `plan.json` / `tfplan.json` in `--source-dir` | Document to evaluate |
| `--plan-file` | | Binary plan from `terraform plan -out=`. Rendered with `terraform show -json` in memory, so no unmasked plan JSON is ever written to disk. Cannot be combined with `--input-path` |
| `--terraform-bin` | auto-detected | terraform/tofu binary for `--plan-file`, preferring the real binary over a CI wrapper |
| `--input-kind` | `terraform_plan` | One of `terraform_plan`, `terraform_state`, `kubernetes`, `json`. Decides how the document is masked |
| `--state-path` | | Optional terraform state, masked before upload |
| `--infracost-path` | | Optional `infracost breakdown --format json` document |
| `--source-dir` | `.` | Terraform source to pack alongside the documents |
| `--no-source` | | Send only the documents. Discovery still looks in `--source-dir` (or `.`) for the plan |

### Run

| Flag | Default | What it does |
|---|---|---|
| `--sha` | | Commit SHA, used to namespace the uploaded archive |
| `--artifact-tag` | `default` | Namespaces the archive within a commit. Needed only when one workflow evaluates the same commit more than once — a plan phase and a state phase, or matrix legs sharing a workflow |
| `--trigger-details-json` | `{"type": "cli"}` | JSON object describing what triggered this run |
| `--trigger-details-file` | | File containing that JSON object |
| `--timeout` | `1800` | Seconds to wait for the run |

### Output

| Flag | Default | What it does |
|---|---|---|
| `--output-json` | | Write the result document here |
| `--output-markdown` | | Write a markdown report here |
| `--comment-marker` | | Opaque first line of the markdown, so a script can find its own comment |
| `--markdown-limit` | `60000` | Truncate the markdown to this length |
| `--fail-on-error` | off | Exit non-zero when a policy fails. An unreachable platform or a run that produced no verdict always exits non-zero regardless of this flag |
