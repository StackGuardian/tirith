# Validate a policy

`tirith lint` reads the engine's own registries and reports mistakes that would otherwise surface
as a confusing verdict. It needs no extra, makes no network call, and runs before anything is
evaluated.

```bash
tirith lint .tirith/policies      # a file, a directory, or a glob
tirith lint --json                # the same report, for a script
tirith lint --gotchas             # the traps below, from the source of truth
```

## Exit codes

| Exit | Meaning |
| --- | --- |
| `0` | Every policy is clean |
| `3` | A policy has an error |
| `1` | A path could not be read |

Warnings alone do not fail the run. `3` rather than `1` for a bad policy is deliberate and matches
the rest of Tirith: the linter saying no about a policy is a verdict, not a tool failure. That
makes it usable as a CI step as much as a self-check.

## What it catches

| Trap | Why it matters |
| --- | --- |
| An invented condition type | There is no `Exists`, `Matches` or `In`. The engine returns an unknown type as an ordinary failed check, so it reads as a real violation. |
| A key from the wrong provider | `terraform_plan` reads `terraform_resource_attribute`; `kubernetes` reads `attribute_path`. An unrecognised key is ignored, not rejected, so the evaluator reads nothing. |
| An operation that does not ship | `jmespath` and `jq_query` appear in test fixtures. Neither exists. |
| `error_tolerance` in the wrong place | It belongs inside `condition`. Anywhere else it has no effect and the policy quietly loses its tolerance. |
| An evaluator nothing references | If `eval_expression` never names it, it cannot affect the verdict, however carefully it was written. |
| A single `&` where `&&` was meant | `&` and `\|` are not supported operators. |

## Add it to CI

Linting is cheap and catches a broken policy before it is ever evaluated against real
infrastructure:

```yaml
- run: pip install "git+https://github.com/StackGuardian/tirith.git@1.0.5"
- run: tirith lint .tirith/policies
```

## What it cannot tell you

Linting checks the **shape**. Only evaluation checks the **meaning**. A policy whose
`provider_args` match no resource at all is structurally perfect and lints clean — and it gates
nothing. Always follow a lint with a run: `reference/verdicts.md`.
