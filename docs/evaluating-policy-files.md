# Evaluating policy files in your repository

`tirith -policy-path … -input-path …` evaluates the policies committed in your repository. It needs no
account and makes no network calls, and it is the surface most open-source users are on.

```
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

This page is about the flags that make it usable as a **CI gate**: several policies at once, the input
masked before its values reach a pull-request comment, and the verdict written out for a job to
publish. The alternative is
[`tirith platform check`](platform-check.md), which evaluates the policies a StackGuardian organization
enforces instead — and writes the [same result document](output-contract.md), so a CI integration built
against one works unchanged against the other.

## Several policies at once

`-policy-path` accepts a file, a **directory** or a **glob**.

- **A file** is evaluated as given. Naming one explicitly is an instruction, so "that is not a policy"
  is reported rather than the file being skipped.
- **A directory** is searched recursively for `*.tirith.json`. If it holds none, any `.json` file
  *shaped* like a policy is used — an object with both `meta` and `evaluators`.
- **A glob** is expanded and filtered by that same shape test.

The shape test is load-bearing rather than defensive: a policy directory routinely also holds the
document under evaluation. Without it, `plan.json` is evaluated *as a policy*, which reports a spurious
failure and buries the real findings.

`-var-path` and `-var` apply to every policy evaluated, so a parameterised policy behaves the same
whether you name the file or the directory holding it.

**No policy files found is an error, not a skip.** Pointed at a path with nothing in it, the command
exits `1`. A green result for a change nothing was evaluated against is the outcome this must never
produce, and "no policies found" is a configuration mistake rather than a deliberate skip.

## Masking, and why it is opt-in

`--input-kind` says what the document is, and supplying it **masks** the document before evaluation:
values terraform marked sensitive are replaced, root `variables` are dropped, `prior_state` is removed.

It matters even though nothing is uploaded. Evaluator messages embed the actual attribute values they
compared, and those messages are copied verbatim into whatever comment or note your CI job posts — so
an unmasked run publishes plan values to a code host. Masking also keeps this verdict identical to
`platform check`'s for the same plan, because that path evaluates the masked document too.

It is opt-in because masking changes the evaluator messages, and those messages are this command's
`--json` output, which is a frozen contract. With no `--input-kind` the file is read exactly as it
always has been.

`terraform_plan` and `terraform_state` are masked. `kubernetes` and `json` are passed through
untouched: they carry no sensitivity markers to mask by, and tirith reads YAML for them, which a JSON
round-trip would break.

## Writing the verdict out

| | |
|---|---|
| `--output-json PATH` | The result document, in the [same shape](output-contract.md) `platform check` writes |
| `--output-markdown PATH` | A rendered report, for a pull-request comment or a merge-request note |
| `--comment-marker TEXT` | An opaque first line for the markdown, so a job can find and edit its own comment |
| `--markdown-limit N` | Truncate the markdown. Default 60000 |
| `--sha SHA` | The revision the findings describe, shown in the report |

Both files are written on **every** exit path, including failures, and the markdown always begins with
`--comment-marker` when one is given. That matters to any caller that edits a sticky comment in place:
writing nothing on the failure path means the caller falls through to a body of its own with no marker
in it, and PATCHing that over a good comment orphans it permanently. It has happened.

Nothing in this group changes what the command prints.

## Exit codes

| Code | Condition |
|---|---|
| 0 | Policies passed or warned. Also a failing policy without `--fail-on-error` |
| 1 | No policy files found; the input was missing or unparseable; a policy could not be evaluated; nothing was evaluated |
| 3 | A policy failed, with `--fail-on-error` |
| 130 | Interrupted |

**A policy that could not be evaluated exits `1` regardless of `--fail-on-error`.** "Could not
evaluate" is tool health, not a policy decision. Such a policy also appears in the report as a visible
failure carrying its reason, so it is never mistakable for a pass and never silently dropped.

**A run of nothing but skips exits `1`.** If every check was swallowed by its `error_tolerance` —
usually because the resources the policies name are not in the document — then nothing was examined,
and this command has always called that a failure rather than a pass. Note this is a deliberate
difference from `platform check`, which counts skips separately and reports them as a pass.

## Flags

The full surface, as the command prints it:

    usage: tirith [-h] [-policy-path PATH] [-input-path PATH] [-var-path PATH] [-var PATH] [--json]
                  [--verbose] [--fail-on-error] [--version] [--input-kind KIND] [--state-path PATH]
                  [--sha SHA] [--output-json PATH] [--output-markdown PATH] [--comment-marker TEXT]
                  [--markdown-limit N]

    Tirith (StackGuardian Policy Framework)

    options:
      -h, --help              show this help message and exit
      -policy-path PATH       Path containing Tirith policy as code
      -input-path PATH        Input file path
      -var-path PATH          Variable file path(s)
      -var PATH               Inline variable(s)
      --json                  Only print the result in JSON form (useful for passing output to other programs)
      --verbose               Show detailed logs of from the run
      --fail-on-error         Exit 3 when a policy fails, instead of 0. Off by default for compatibility.
      --version               show program's version number and exit

    reporting:
      Write the verdict out for a CI job to publish. All optional.

      --input-kind KIND       terraform_plan, terraform_state, kubernetes or json. Masks the input before evaluating
      --state-path PATH       Terraform state, when --input-kind is terraform_state
      --sha SHA               Revision these findings describe, recorded in the report
      --output-json PATH      Write the result document here (same shape as `tirith platform check`)
      --output-markdown PATH  Write a markdown report here, for a comment or a note
      --comment-marker TEXT   Opaque first line of the markdown, for comment stickiness
      --markdown-limit N      Truncate the markdown to this length. Default: 60000
