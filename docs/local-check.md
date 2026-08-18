# `tirith local check`

Evaluate the policy files committed in your repository against a terraform plan, state document or
JSON document. No credentials, no network calls.

It is the credential-free counterpart of
[`tirith platform check`](platform-check.md) and writes the *same* report, in the
[same shape](output-contract.md) — so a CI integration built against one works unchanged against the
other. Adding a StackGuardian organization later changes which policies apply, not how anything is
wired.

```
tirith local check --policy-path .tirith/policies --input-path plan.json --fail-on-error
```

## What it does

1. **Discovers policies** at `--policy-path`.
2. **Masks the document**, exactly as platform mode does. Nothing is uploaded, so this is not about
   transport — evaluator messages embed the values they compared, and those messages are copied
   verbatim into whatever pull-request comment or merge-request note the caller posts. An unmasked
   local run publishes plan values to a code host. Masking also keeps a local verdict identical to
   the platform one for the same plan, because platform mode evaluates the masked document too.
3. **Evaluates each policy** in a subprocess, against tirith's frozen `--json` output contract.
4. **Writes the verdict**, optionally as JSON and markdown for a later CI step.

## It is never entered implicitly

`tirith platform check` with no credentials is an error, not a silent fallback to this command. A
fallback would evaluate whatever happens to be committed and report green when a token was simply
misspelled — the exact failure a policy gate exists to prevent. A CI integration that wants "no
credentials therefore local" makes that choice itself, deliberately, and can say so in its own log.

For the same reason this command rejects every credential, workflow, archive and run flag rather than
accepting and ignoring them. A credential-shaped flag that silently does nothing is how someone ends
up with a green check their organization's policies never saw.

## Policy discovery

`--policy-path` accepts a file, a directory or a glob, and defaults to `.tirith/policies`.

- **A file** is taken as given. Naming one explicitly is an instruction, so "that is not a policy" is
  reported rather than the file being skipped.
- **A directory** is searched recursively for `*.tirith.json`. If it holds none, any `.json` file
  *shaped* like a policy is used — an object with both `meta` and `evaluators`.
- **A glob** is expanded and filtered by that same shape test.

The shape test is load-bearing, not defensive: a policy directory routinely also holds the document
under evaluation. Without it, `plan.json` is evaluated *as a policy*, which reports a spurious failure
and buries the real findings.

**No policy files is an error.** Pointed at a path with nothing in it, the command exits `1` rather
than reporting a pass. A green result for a change nothing was evaluated against is the one outcome
this mode must never produce, and "no policies found" is a configuration mistake rather than a
deliberate skip.

## Enforcement

A failing policy fails. `meta.enforcement` downgrades it to a warning for these values:

`soft_mandatory`, `advisory`, `warn`, `warning`, `low`, `approval_required`, `approval-required`,
`approval`

and gates for these:

`hard_mandatory`, `mandatory`, `fail`, `error`, `high`, `critical`, `blocking`

The approval spellings warn rather than gate, matching platform mode, where a policy carrying
`onFail: APPROVAL_REQUIRED` also warns — the run finishes before the intent is known, so there is
nothing to approve. Local mode has no approval mechanism at all, so failing closed on it would block a
change with no way to unblock it.

Anything else gates *and* raises a warning naming the value, in the log and in `policy_warnings` in
the result document. An unlabelled or mislabelled policy must gate rather than slip through, but a
typo in `enforcement` silently becoming policy is worse than a noisy one.

Omitting `meta.enforcement` entirely gates, with no warning.

## Cost policies need the platform

`--infracost-path` is accepted and reported as ignored. Cost evaluation needs a second document
alongside the plan, and this mode evaluates one. Saying so beats evaluating the plan and reporting a
cost policy as unevaluated with no explanation.

## Exit codes

| Code | Condition |
|---|---|
| 0 | Policies passed or warned. Also a failing policy without `--fail-on-error` |
| 1 | No policy files found; the input document was missing or unparseable; a policy could not be evaluated; no verdict was produced |
| 3 | A policy failed, with `--fail-on-error` |
| 130 | Interrupted |

**A policy that could not be evaluated exits `1` regardless of `--fail-on-error`.** "Could not
evaluate" is tool health, not a policy decision, so the flag does not govern it — the same reason an
unreachable platform ignores it in the other mode. Such a policy also appears in the report as a
visible failure carrying its reason, so it is never mistakable for a pass and never silently dropped.

Note the `2` documented for platform mode (a run timeout) is unreachable here: there is no run to
time out. The per-policy timeout is 300 seconds, and a policy that hits it is one entry in
`policy_errors` among possibly several verdicts, so it exits `1`.

## Both output files are always written

`--output-json` and `--output-markdown` are written on **every** exit path, including failures, and
the markdown always begins with `--comment-marker` when one is given.

This matters to any caller that edits a sticky comment in place: writing nothing on the failure path
means the caller falls through to a body of its own with no marker in it, and PATCHing that over a
good comment orphans it permanently. It has happened. Writing both files also puts the reason on the
merge request rather than only in the job log.

## Flags

The full surface, as the command prints it:

    usage: tirith local check [-h] [--policy-path POLICY_PATH] [--input-path INPUT_PATH]
                              [--plan-file PLAN_FILE] [--terraform-bin TERRAFORM_BIN]
                              [--input-kind {terraform_plan,terraform_state,kubernetes,json}]
                              [--state-path STATE_PATH] [--infracost-path INFRACOST_PATH]
                              [--source-dir SOURCE_DIR] [--sha SHA] [--output-json OUTPUT_JSON]
                              [--output-markdown OUTPUT_MARKDOWN] [--comment-marker COMMENT_MARKER]
                              [--markdown-limit MARKDOWN_LIMIT] [--fail-on-error]

    Masks the document, evaluates every policy found at --policy-path, and writes the same result
    document and markdown report that `tirith platform check` writes. Requires no credentials and
    makes no network calls.

    options:
      -h, --help            show this help message and exit

    policies:
      --policy-path POLICY_PATH
                            A policy file, a directory, or a glob. A directory is searched
                            recursively for *.tirith.json, or failing that for any .json file shaped
                            like a policy. Default: .tirith/policies

    inputs:
      --input-path INPUT_PATH
                            Document to evaluate. Default: plan.json or tfplan.json.
      --plan-file PLAN_FILE
                            Binary terraform plan, rendered in memory. Not with --input-path.
      --terraform-bin TERRAFORM_BIN
                            terraform/tofu binary used for --plan-file.
      --input-kind {terraform_plan,terraform_state,kubernetes,json}
                            What the document is.
      --state-path STATE_PATH
                            Terraform state, when --input-kind is terraform_state.
      --infracost-path INFRACOST_PATH
                            Accepted and ignored: cost policies need a second document, so they need
                            platform mode.
      --source-dir SOURCE_DIR
                            Where to look for the document. Default: .

    run:
      --sha SHA             Revision these findings describe, recorded in the report.

    output:
      --output-json OUTPUT_JSON
                            Write the result document here.
      --output-markdown OUTPUT_MARKDOWN
                            Write a markdown report here.
      --comment-marker COMMENT_MARKER
                            Opaque first line of the markdown, for stickiness.
      --markdown-limit MARKDOWN_LIMIT
                            Truncate the markdown to this length.
      --fail-on-error       Exit non-zero when a policy fails. A policy that could not be evaluated
                            at all always exits non-zero regardless of this flag.

`--input-kind kubernetes` and `--input-kind json` are passed through unmasked: they carry no
sensitivity markers to mask by, and tirith reads YAML for them, which a JSON round-trip would break.
Both require `--input-path`.
