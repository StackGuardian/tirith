---
name: tirith-migrate
description: Translate existing policy-as-code into Tirith policies. HashiCorp Sentinel today; Checkov, OPA/Rego and conftest are planned. Use when asked to migrate, convert, port or translate policies to Tirith, when a repository contains .sentinel files or a sentinel.hcl, or when asked what a Sentinel policy would look like in Tirith. Requires the tirith-policies skill for the target vocabulary.
---

# Migrate policies to Tirith

A migration is a projection from a larger language onto a smaller one. Sentinel and Rego are
programs; a Tirith policy is JSON that names a provider, a value, and a condition. Most real
policies fit. Some do not, and the failure mode is quiet: a translation that parses, looks right,
and gates nothing. **This skill exists to say which is which before any JSON is written.**

## Vocabulary comes from `tirith-policies`

Do not translate from memory. Read `../tirith-policies/reference/schema.md` for the closed list of
providers, operations, argument keys and the thirteen condition types. If that skill is not
installed, fetch `https://stackguardian.github.io/tirith/llms.txt` and follow it to the schema
page. Everything below assumes that vocabulary.

## Per-source references

| Source | Reference | Status |
| --- | --- | --- |
| HashiCorp Sentinel | `reference/sentinel.md`, corpus in `reference/sentinel-corpus.md` | Measured against 110 public policies |
| Checkov | | Planned |
| OPA / Rego, conftest | | Planned |

## The protocol

1. **Inventory.** List every source policy. Read the policy-set manifest (`sentinel.hcl`) for
   enforcement levels and parameters. Note which policies are registered twice with different
   parameters; they translate once.
2. **Classify before translating.** For each policy, name its pattern from the source reference
   and assign a fidelity:
   - `exact`: a Tirith policy returns the same verdict on every plan.
   - `approximate`: expressible, but stricter or looser in a case you can name.
   - `not expressible`: needs something Tirith lacks. Name it, and link the tracking issue.
3. **Translate `exact` and `approximate`.** Carry `meta.name` from the source policy name, put the
   Sentinel enforcement level in `meta.enforcement`, and map every `param` to `{{ var.NAME }}`.
4. **Refuse `not expressible` in words.** Write what the policy does, what Tirith cannot see, and
   the issue that would change that. Do not write a policy that checks something adjacent.
5. **Verify every translation against the source's own tests.** Sentinel policies ship mocks under
   `test/<policy>/`. Transcribe the failing mock into `should-fail.json` and the passing one into
   `should-pass.json` (the mocks already have the `resource_changes` shape). Run both:
   ```bash
   tirith -policy-path policy.json -input-path should-fail.json --fail-on-error; echo $?   # 3
   tirith -policy-path policy.json -input-path should-pass.json --fail-on-error; echo $?   # 0
   ```
   For an `approximate` translation, also write `diverges.json`: a plan where the source and the
   translation disagree. The reviewer needs to see the divergence, not read about it.
6. **Hand back a report**, one row per source policy: name, fidelity, Tirith file, and one line
   on what changed. Fidelity is the column the reader looks at first.

## Rules that hold for every source

- A Tirith evaluator yields one result per matching resource and fails if any fails. That is the
  universal quantifier. There is no existential: "at least one resource satisfies X" does not map.
- `eval_expression` combines evaluator verdicts, each already collapsed across all resources. It
  cannot bind two tests to the same resource or the same nested block. "Where type is ingress,
  cidr must not be open" becomes "no block may have cidr open", which is stricter. Say so.
- `attribute` reads `change.after` only. Anything about the previous value, a destroyed resource,
  or a value unknown until apply is invisible.
- Configuration is not the plan. Module sources, variables, outputs, provisioners and expression
  references live in `tfconfig`; Tirith reads none of them.
- A plan that destroys a resource of the checked type currently turns the evaluator's verdict to
  `null` (Tirith issue #293). Test with plans that do not destroy, and warn the reader.

## Before you hand it back

1. Did every policy get a fidelity before it got JSON?
2. Does every `approximate` row name the case where verdicts differ, and ship `diverges.json`?
3. Does every `not expressible` row link a Tirith issue or say "not tracked"?
4. Did every translated policy exit `3` on `should-fail.json` and `0` on `should-pass.json`?
5. Is every `param` a `{{ var.NAME }}` with a `variables.json` beside the policy?
6. Is every condition type and argument key taken from `schema.md`, not recalled?

## Worked examples

`examples/sentinel/` holds five translations from the idioms of HashiCorp's public policy
libraries, each with its Sentinel source, the Tirith policy, and the plans that prove it:

| Example | Fidelity | Shows |
| --- | --- | --- |
| `restrict-instance-type` | exact | `filter_attribute_not_in_list` to `ContainedIn`; `param` to `-var` |
| `mandatory-tags` | exact | Tag keys via `Contains` on the map; one evaluator per key and type |
| `prevent-database-destroy` | exact | `action` emits one result per action; `NotEquals "delete"` catches deletes and replacements |
| `restrict-ssh-ingress` | approximate | The per-block conjunction collapses to a stricter rule |
| `require-private-registry-modules` | not expressible | A `tfconfig` policy, refused in words |
