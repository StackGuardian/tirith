# Starter policies

Seven rules that are worth putting in front of a Terraform or OpenTofu pipeline on day one, and a
sample input for each that trips it. Everything here runs with no cloud account and no network call.

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"

# a rule against the input built to trip it
tirith -policy-path policies/03-block-destroy.json \
       -input-path  inputs/03-block-destroy.fails.json --fail-on-error
# → exit 3, naming aws_db_instance.orders and the action that tripped it

# and the same rule against a plan with nothing wrong with it
tirith -policy-path policies/03-block-destroy.json \
       -input-path  inputs/00-clean-plan.passes.json --fail-on-error
# → exit 0
```

Every policy here has been run both ways. See [Verification](#verification).

### Rules a per-resource engine cannot express

| | Policy | Sev | Reads | Why it needs a whole-plan engine |
|---|---|---|---|---|
| 03 | `block-destroy` | critical | `action` | 17 stateful types. A replacement plans as `["delete","create"]`, so this catches the case that reads like an edit |
| 08 | `provider-version-pinned` | medium | `provider_config` | A fact about the provider block, not any resource. `>= 5.0` is how a provider major arrives on a Monday and rewrites 200 resources |
| 11 | `prohibited-resource-types` | medium | `count` | `count == 0` is an assertion about the plan. When the answer is "none, correctly", there is no resource to hang a finding on |
| 04 | `allowed-regions` | medium | `provider_config` | Also a provider-block fact |
| 05 | `minimum-terraform-version` | low | `terraform_version` | A fact about the run, not the code |
| 10 | `root-module-size` | low | `count` | A property of the whole module |

### Rules everyone needs, which other tools also do well

Included because a starter pack has to be usable, not because they are differentiators.

| | Policy | Sev | Catches |
|---|---|---|---|
| 01 | `required-tags` | low | a resource with no owner — including the blank-string case, which is the one that survives review |
| 02 | `public-access-blocked` | high | a public access block that closes only some of the four vectors |
| 06 | `database-safeguards` | high | an unencrypted database, or one deletable by accident |
| 09 | `no-credentials-in-resolved-values` | critical | a key reaching the plan through a variable default — invisible in the resource block, fully resolved here |
| 12 | `no-open-ingress` | high | `0.0.0.0/0`, in both the legacy and current rule resources |
| 07 | `cost-ceiling` | medium | a change that blows the budget (needs an Infracost breakdown) |

## Four things in here that are easy to get wrong

**`03` catches replaces, not just destroys.** Terraform plans a replacement as
`["delete", "create"]`, so a rule that checks for `delete` catches both. This is the rule that has no
static-analysis equivalent: nothing in your `.tf` files says *this change will destroy the database*,
because that depends on what is already running.

**`04` skips rather than fails when it cannot see the region.** Tirith reads
`expressions.region.constant_value` off the provider block, so a repository writing
`region = var.region` produces a severity-2 read error. `error_tolerance: 2` turns that into a skip.
That is the point: **a rule that could not read the value must not report a pass it did not earn.**

**`05` uses `RegexMatch`, and must.** `GreaterThanEqualTo` is a plain Python `>=`, so on version
strings it compares lexicographically — `"1.9.0" >= "1.11.4"` is `True`, and a naive minimum-version
rule would pass everything forever. Note also that `terraform_version` is the version that *ran the
plan*, a runtime fact, not the `required_version` constraint in your source.

**`07` needs a different input.** It reads an Infracost breakdown, not a plan. The GitHub Action
ignores Infracost in local mode with a warning, so without an Infracost step this rule reports
nothing — which is honest, and worth knowing before you wonder why it is quiet.

## Two rules that are deliberately absent

**"State must be remote."** Not possible here, and not a gap in Tirith: `terraform show -json`
contains no backend block at all — `format_version`, `terraform_version`, `variables`,
`planned_values`, `resource_changes`, `output_changes`, `prior_state`, `configuration`, and nothing
else. A local-state finding belongs to a scan of the source, which is a different evidence source
answering a different question. Putting it here would mean inventing a check that silently never fires.

**"No public buckets", as a guarantee.** `02` verifies that the public access blocks you *declared*
close all four vectors. Proving every bucket *has* one needs the `direct_references` operation, which
is worth adding — it is the shape of check that static analysis handles worst and Tirith handles best.
The rule is named for what it actually does rather than what would sell better.

## Error severities, and how to choose `error_tolerance`

Undocumented anywhere else, and the thing most likely to make a rule lie. `error_tolerance` skips read
problems **at or below** its value; skipped checks leave `eval_expression` entirely.

| Severity | Raised when | Set tolerance to |
|---|---|---|
| **0** | `change.after` is `null` — the resource is being **deleted** | anything; a delete has no attributes to read |
| **1** | the resource type is not in this plan at all | `1`, so a plan without databases skips the database rules |
| **2** | the attribute is not on the resource | `0` if absence *is* the violation (a missing tag), `2` if the rule only applies where the field exists |
| **99** | the policy is malformed | never tolerate; fix the policy |

Severity 0 is why no attribute rule can inspect a resource being destroyed — `after` is `null`. That is
an engine limit, not a policy mistake. Tracked in [ROADMAP.md](../ROADMAP.md).

## Pending engine support

[`policies-pending/`](policies-pending/) holds two rules that **do not run yet** — a blast-radius gate
and a deletion-protection-removed detector. Each needs a small engine change, both tracked in
[ROADMAP.md](../ROADMAP.md):

- **blast radius** needs `count` to filter by action. It matches on `terraform_resource_type` only, and
  Terraform reports unchanged resources as `no-op` entries, so `count(*)` returns the size of the root
  module rather than the size of the change. `inputs/10-root-module-size.fails.json` is 240 resources
  of which 238 are no-ops — the number a blast-radius rule wants is 2.
- **deletion-protection-removed** needs `change.before`. The `attribute` operation reads `change.after`,
  so a policy can see a value but never a transition — and on a delete, `after` is `null`.

They are staged here so each policy and the change that enables it can be reviewed together, and kept
out of `policies/` so nothing runs them by accident or counts them as working. `validate.py` enforces
that separation in both directions.

**If you want either rule, say so on the issue** — a policy someone is waiting for is a better argument
for an engine change than a maintainer's hunch.

## Verification

Every policy in `policies/` was run against real Tirith at `1.2.0`, in both directions:

| | Result |
|---|---|
| 13 policies against their own `*.fails.json` | **13 exit 3** — each fails the way it was designed to |
| 11 plan policies against `inputs/00-clean-plan.passes.json` | **11 exit 0** — no false positives |
| `04-allowed-regions` against `04-allowed-regions.skips.json` | **exit 1**, `SKIPPED: region is not found in the provider_config (severity_value: 2)` |

That third row is the one worth reading twice. The region is set from a variable, so the rule cannot
see it — and it reports *skipped*, not passed. A rule that could not read its input must never look
like a rule that was satisfied.

Reproduce the whole set:

```bash
for p in examples/policies/*.json; do
  n=$(basename "$p" .json)
  i="examples/inputs/$n.fails.json"
  [ -f "$i" ] || continue
  tirith -policy-path "$p" -input-path "$i" --fail-on-error >/dev/null 2>&1
  echo "$n -> exit $?   (3 expected)"
done
```

## Checking your own additions

```bash
python3 examples/validate.py
```

Run it before opening a pull request that adds a policy.

Confirms every condition and operation exists, that `eval_expression` references only declared ids and
uses all of them, that `error_tolerance` sits inside `condition` where it belongs, that no numeric
comparison is pointed at a version string — and that each policy's sample input contains something the
rule would actually look at.

It also rejects any `provider_args` key the engine does not read — the failure that has no symptom,
because the handler ignores unknown keys and the rule silently constrains nothing.

It reports expected warnings on `03` and `09`: the sample plans hold only some of the covered types, so
the rest skip. That is `error_tolerance: 1` doing its job, and seeing it in the output is more useful
than a clean run.

## Adding a rule

`evaluators` are the checks; `eval_expression` combines them with `&&`, `||` and `!`. Thirteen
conditions exist: `Equals` `NotEquals` `Contains` `NotContains` `ContainedIn` `NotContainedIn`
`IsEmpty` `IsNotEmpty` `LessThan` `LessThanEqualTo` `GreaterThan` `GreaterThanEqualTo` `RegexMatch`.

For a plan, seven operations: `attribute` `action` `count` `direct_dependencies` `direct_references`
`terraform_version` `provider_config`.

Set `meta.severity` — `critical`, `high`, `medium`, `low` — on anything you add. It is what makes a set
of rules orderable once there are more than a handful.
