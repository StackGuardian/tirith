# Evaluation Expressions

Source: https://stackguardian.github.io/tirith/docs/tirith-reference/eval-expressions/
Summary: Reference for eval_expression, the boolean expression that combines evaluator results into a policy's final verdict.

A policy's top-level `eval_expression` is a boolean expression over the `id`s of its evaluators. After every evaluator has produced its verdict, Tirith substitutes those verdicts into the expression and evaluates it; the outcome becomes `final_result` in the output.

```json
{
  "meta": { "version": "v1", "required_provider": "stackguardian/json" },
  "evaluators": [
    { "id": "check_region",  "provider_args": { "...": "..." }, "condition": { "...": "..." } },
    { "id": "check_tags",    "provider_args": { "...": "..." }, "condition": { "...": "..." } },
    { "id": "check_budget",  "provider_args": { "...": "..." }, "condition": { "...": "..." } }
  ],
  "eval_expression": "(check_region || check_tags) && check_budget"
}
```

## Referencing evaluators

Evaluators are referenced by their `id`, written bare (no quotes, no prefix). Substitution matches ids as whole words, so one id being a prefix of another (`check` and `check_2`) is not a problem.

Use only letters, digits, and underscores in ids that appear in the expression. An id with other characters (such as `-`) still works *if it is defined*, because it is replaced by its verdict before the expression is parsed — but if such an id is missing from the policy, the leftover text cannot be parsed as an expression and the whole run aborts (see [Unparseable expressions](#unparseable-expressions)).

Each id stands for the tri-state verdict of its evaluator:

- `true` — every value it checked passed,
- `false` — at least one value failed,
- *skipped* — the evaluator did not actually check anything (all of its provider errors were within `error_tolerance`).

## Operators

| Operator | Meaning | Example |
| --- | --- | --- |
| `&&` | logical AND | `check_a && check_b` |
| `\|\|` | logical OR | `check_a \|\| check_b` |
| `!` | logical NOT | `!check_a` |
| `( )` | grouping | `(check_a \|\| check_b) && check_c` |

Whitespace is ignored. There are no comparison operators, literals, or function calls — only ids, the three operators above, and parentheses.

**Precedence**, from tightest to loosest: `!`, then `&&`, then `||`. Both of these hold (verified against the implementation):

- `a || b && c` means `a || (b && c)` — with `a` true and `b`, `c` false, the expression is true.
- `!a || b` means `(!a) || b` — with `a` and `b` both true, the expression is true.

Use parentheses whenever the intent is not obvious.

**Single `&` and `|` are rejected.** They are not silently treated as `&&`/`||`; the run aborts with an explicit error and exit code 1:

```
Unsupported operator '&' in eval_expression. Use '&&' instead.
```

## Skipped evaluators

An evaluator whose verdict is *skipped* (`passed: null` in the output) is **removed from the expression** before evaluation, together with any `!` that applied to it, rather than being treated as false:

- `skipped && other` reduces to `other`;
- `!skipped && other` also reduces to `other`;
- if *everything* in the expression is removed, `final_result` is `null` — see below.

This is deliberate: treating a skipped check as `false` would fail policies through `!`-negations, and treating it as `true` would pass checks that never ran.

## Missing evaluator ids

An id used in the expression but not defined by any evaluator does **not** abort the run. It is removed from the expression the same way a skipped evaluator is, the rest of the expression is evaluated normally, and a note is appended to the top-level `errors` array of the output:

```
The following evaluator ids are not defined and have been removed: ghost_check
```

`errors` is informational: it does not affect `final_result` or the exit code. A policy whose expression is `real_check && ghost_check` passes with `final_result: true` and exit code 0 when `real_check` passes. Watch the `errors` array — a typo in an id silently weakens the policy.

The reverse — an evaluator defined but never mentioned in the expression — still runs and appears in the output, but its verdict does not influence `final_result`.

## Unparseable expressions

If the expression cannot be parsed at all — a syntax error such as `check1 &&`, an empty string, a single `&`/`|`, or leftover text from a missing id that is not a valid identifier — the evaluation **aborts**: no result document is produced (with `--json`, the output is `{}`), and the process exits with code **1** regardless of `--fail-on-error`. This is the "tool error" exit code, distinct from a policy failure.

As a safety measure the expression is evaluated with no access to builtins, and any symbol that survives id substitution is rejected (`The following symbols are not allowed: ...`) with `final_result: false`; the expression language cannot call functions or reach interpreter internals.

## From expression result to exit code

`final_result` is tri-state, and with `--fail-on-error` it maps to the exit code:

| `final_result` | Meaning | Exit code with `--fail-on-error` |
| --- | --- | --- |
| `true` | every check that ran passed the expression | 0 |
| `false` | the expression evaluated to false | 3 |
| `null` | nothing was left to evaluate — every evaluator referenced in the expression was skipped or undefined | 1 |
| *(absent)* | the run aborted before a verdict (unparseable expression, undefined policy variables) | 1 |

Without `--fail-on-error`, the exit code is 0 in all of these cases except an aborted run, which still exits 1; the verdict is only in the output.

`null` is not a pass: a policy whose every check was skipped checked precisely nothing.

## Worked example

```json
"eval_expression": "!deprecated_api_used && (region_allowed || region_exempted)"
```

| `deprecated_api_used` | `region_allowed` | `region_exempted` | `final_result` |
| --- | --- | --- | --- |
| `false` | `true` | `false` | `true` |
| `true` | `true` | `false` | `false` |
| *skipped* | `true` | `false` | `true` — reduces to `(region_allowed \|\| region_exempted)` |
| *skipped* | *skipped* | *skipped* | `null` — exit 1 under `--fail-on-error` |

For what makes an individual evaluator pass, fail, or get skipped, see [Evaluators and Conditions](./evaluators.md).
