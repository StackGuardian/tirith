---
id: output-contract
title: The Result Document
sidebar_label: Result Document
description: The JSON document tirith writes with --output-json, identical whether policies come from your repository or your organization, and the contract CI integrations read it by.
keywords:
  - tirith
  - output
  - json
  - ci
site_name: Tirith
slug: output-contract/
---

`--output-json` writes one document, in one shape, from both
[`tirith platform check`](platform-check.md) and [`tirith -policy-path …`](evaluating-policy-files.md). This page is
the contract, because two integrations read it — the
[GitHub Action](https://github.com/StackGuardian/tirith-iac-governance-action) and the GitLab CI
component — and turn it into comments, statuses and job outputs.

## The rule

**Every key exists in every mode.** A key with no meaning on a path is `null` (or `[]` for the lists),
never omitted and never invented.

Omitting keys per mode would force every consumer to write two parsers, and the one that forgets
reports the wrong thing on the mode it was not tested against. Inventing them is worse: a fabricated
`wfrun_url` in local mode renders as a link to a run that does not exist.

Both documents are built by one function, `tirith.platform.report.result_document`, so the shapes
cannot drift apart by editing one caller.

## Keys

| Key | Platform mode | Local mode |
|---|---|---|
| `mode` | `"platform"` | `"local"` |
| `status` | The workflow run's terminal status: `COMPLETED`, `ERRORED`, `CANCELLED`, `APPROVAL_REQUIRED` | `COMPLETED`, or `ERRORED` when nothing could be evaluated |
| `verdict` | `passed` · `warned` · `failed` · `no-policies` · `errored` | the same five |
| `counts` | `passed`, `failed`, `warned`, `approval_required`, `skipped`, `unknown` | the same six |
| `headline` | The one-line summary, e.g. `Tirith — 2 failed, 1 warned, 5 passed` | the same |
| `policy_results` | The `PolicyEvalResults` document from the run | the same shape, built from the local evaluation |
| `wfrun_id` | The run id | `null` |
| `wfrun_url` | Link to the run in StackGuardian | `null` |
| `monthly_cost` | `totalMonthlyCost` from the cost breakdown, or `null` | `null` — cost needs a second document |
| `archive_key` | Where the uploaded archive lives | `null` — nothing is uploaded |
| `source_packed` | Whether the archive actually holds the terraform source | `false` |
| `source_skipped_reason` | Why it does not, or `null` | `null` |
| `policies_evaluated` | `null` | How many policy files were evaluated |
| `policies_errored` | `null` | How many could not be |
| `policy_path` | `null` | The `--policy-path` that was used |
| `policy_errors` | `[]` | `[{"policy": path, "reason": str}]` |
| `policy_warnings` | `[]` | `[str]` — currently unrecognised `meta.enforcement` values |

## Reading it

**Read `mode` rather than inferring it** from which keys are populated. Inference is what makes
adding a key a breaking change.

**`verdict` is the answer; the exit code is the gate.** They are related but not the same: `failed`
without `--fail-on-error` exits `0` on purpose. A consumer that wants to report the verdict and a
consumer that wants to block are reading two different things.

**`counts.unknown` distinguishes "nothing failed" from "we could not read part of it."** Without it,
an errored run reports `failed: 0`, which a consumer copying counts to its own outputs turns into a
clean bill of health. A non-zero `unknown` is why `verdict` can be `errored` while `failed` is `0`.

**`source_skipped_reason` is truthy only when there is a real reason.** It stays `null` in local mode
rather than carrying a sentinel like `"not_applicable"`, because a consumer's "the terraform source
was not uploaded" warning keys on truthiness — a sentinel would fire it on every local run, about an
upload that was never attempted.

**`policy_errors` is structured so a front end can annotate without scraping stderr.** Everything in
it is also logged, but a log line is not a data source.

## Written on every exit path

Both `--output-json` and `--output-markdown` are written even when the check fails outright, with
`status: "ERRORED"`, `verdict: "errored"`, zeroed counts, and the reason in `policy_errors`. The
markdown carries `--comment-marker` as its first line.

A consumer that edits a sticky comment in place depends on this. When these files were absent on the
failure path, the caller fell through to a body of its own with no marker in it, and PATCHing that
over a good comment orphaned it permanently.
