---
id: evaluators
title: Evaluators and Conditions
sidebar_label: Evaluators
description: Complete reference for all Tirith condition types, their parameters, type handling, and pass/fail semantics.
keywords:
  - tirith
site_name: Tirith
slug: evaluators/
---

Every evaluator in a Tirith policy applies a **condition** to one or more values extracted by a provider. This page is the complete reference for all 13 condition types, including exactly how each one treats strings, numbers, lists, dictionaries, and `null`.

## Anatomy of a condition

An evaluator block looks like this:

```json
{
  "id": "region_check",
  "provider_args": {
    "operation_type": "get_value",
    "key_path": "region"
  },
  "condition": {
    "type": "Equals",
    "value": "eu-central-1"
  }
}
```

The `condition` object accepts three keys:

| Key | Required | Meaning |
| --- | --- | --- |
| `type` | yes | One of the 13 evaluator names listed below. The name is case-sensitive. |
| `value` | yes, except for `IsEmpty` and `IsNotEmpty`, which ignore it | The value the extracted input is compared against. Any JSON type is accepted; each evaluator defines which types it supports. |
| `error_tolerance` | no (default `0`) | The maximum provider error severity that is *skipped* instead of failing the evaluator. See [Error Tolerance](../tirith-policies/tirith-policy-error-tolerance.md). |

Throughout this page:

- **input value** means a value the provider extracted from the input document (`evaluator_input` in the code),
- **condition value** means `condition.value` from the policy (`evaluator_data` in the code).

A provider can return *several* input values for one evaluator (for example, a wildcard `key_path` such as `items.*`). The condition is applied to **each value independently, and the evaluator passes only if every value passes**. If the provider returns no values at all, the evaluator fails with the message `Could not find input value`.

Each evaluator therefore ends in one of three states:

- `passed: true` — every extracted value satisfied the condition,
- `passed: false` — at least one value did not (or an unrecoverable provider error occurred),
- `passed: null` — the evaluation was *skipped*: every provider error was within `error_tolerance` and no value was actually checked.

## Failures versus errors

This distinction matters for exit codes, so it is worth stating precisely:

- **Evaluators never abort the run.** Every condition type catches internal exceptions. A type mismatch — comparing a string with a number, matching a regex against `null`, searching inside a boolean — produces `passed: false` with an explanatory message. It is reported and gated exactly like a genuine policy violation: with `--fail-on-error`, `final_result: false` exits with code **3**.
- Exit code **1** (a tool error rather than a verdict) is reserved for problems outside the evaluators: an unreadable policy or input file, undefined policy variables, an `eval_expression` that cannot be parsed (see [Evaluation Expressions](./eval-expressions.md)), or a run in which every evaluator was skipped (`final_result: null`).
- A misconfigured evaluator — an unsupported `condition.type` or an unsupported provider `operation_type` — is surfaced as an ordinary failed evaluator (`passed: false`) with an explanatory message, so under `--fail-on-error` it exits **3**, not 1.

Without `--fail-on-error`, the process exits **0** regardless of the verdict; the verdict is only in the output.

## Quick reference

| `condition.type` | Passes when | `condition.value` | On a type mismatch |
| --- | --- | --- | --- |
| [`Equals`](#equals) | input value equals the condition value | any JSON | returns false (values of different types are simply not equal) |
| [`NotEquals`](#notequals) | input value differs from the condition value | any JSON | returns true (different types are not equal) |
| [`GreaterThan`](#comparisons-greaterthan-greaterthanequalto-lessthan-lessthanequalto) | `input > condition value` | number, string, or list (same type as input) | returns false, message carries the comparison error |
| [`GreaterThanEqualTo`](#comparisons-greaterthan-greaterthanequalto-lessthan-lessthanequalto) | `input >= condition value` | same | same |
| [`LessThan`](#comparisons-greaterthan-greaterthanequalto-lessthan-lessthanequalto) | `input < condition value` | same | same |
| [`LessThanEqualTo`](#comparisons-greaterthan-greaterthanequalto-lessthan-lessthanequalto) | `input <= condition value` | same | same |
| [`IsEmpty`](#isempty) | input is `null`, `""`, `[]`, or `{}` | ignored | returns false for numbers and booleans (never an error) |
| [`IsNotEmpty`](#isnotempty) | input is a **non-empty string, list, or dictionary** | ignored | returns false for numbers, booleans, and `null` |
| [`RegexMatch`](#regexmatch) | the pattern is found in the input | string (regular expression) | returns false for non-string/list/dict input; invalid pattern returns false with the regex error message |
| [`ContainedIn`](#containedin) | the input value occurs inside the condition value | string, list, or dictionary | returns false with an "unsupported data type" message |
| [`NotContainedIn`](#notcontainedin) | the input value does **not** occur inside the condition value | string, list, or dictionary | returns false (not true) with an "unsupported data type" message |
| [`Contains`](#contains) | the condition value occurs inside the input value | any JSON (input must be string, list, or dictionary) | returns false with an "unsupported data type" message |
| [`NotContains`](#notcontains) | the condition value does **not** occur inside the input value | any JSON (input must be string, list, or dictionary) | returns false (not true) with an "unsupported data type" message |

Note the last two rows of each pair: **the `Not*` variants are not simple negations.** When the data has a type the evaluator does not support, *both* the positive and the negative form fail. If a value may be absent or of an unexpected type, test that explicitly (for example with `IsNotEmpty`) instead of relying on a `Not*` condition to pass.

---

## Equals

Passes when the input value equals the condition value.

- Comparison is by value, with one normalization: **lists of scalars are sorted before comparing**, recursively, including lists nested inside dictionaries. `[1, 2]` equals `[2, 1]`, and `{"a": [2, 1]}` equals `{"a": [1, 2]}`. A list that mixes types (for example `[1, "a"]`) cannot be sorted and is compared in its original order.
- Numbers compare numerically: `1` equals `1.0`.
- Booleans compare as the numbers 1 and 0: `true` equals `1` and `false` equals `0`.
- Strings never equal numbers: `"1"` is **not** equal to `1`.
- `null` equals `null`.
- Dictionaries compare by keys and values; key order never matters.

A type mismatch is not an error; the values are simply unequal and the check fails.

```json
"condition": { "type": "Equals", "value": ["b", "a"] }
```

| Input value | Result |
| --- | --- |
| `["a", "b"]` | passes (list order ignored) |
| `["a", "b", "c"]` | fails |
| `"a,b"` | fails |

## NotEquals

The exact negation of [`Equals`](#equals), using the same normalization. It passes whenever `Equals` would fail, including on type mismatches: `"1"` NotEquals `1` passes.

```json
"condition": { "type": "NotEquals", "value": "0.0.0.0/0" }
```

An input value of `"10.0.0.0/16"` passes; `"0.0.0.0/0"` fails.

## Comparisons: GreaterThan, GreaterThanEqualTo, LessThan, LessThanEqualTo

Each passes when `input value <operator> condition value` holds:

| Type | Operator |
| --- | --- |
| `GreaterThan` | `>` |
| `GreaterThanEqualTo` | `>=` |
| `LessThan` | `<` |
| `LessThanEqualTo` | `<=` |

Supported operand combinations (both sides must be of a comparable type):

- **numbers** with numbers — the usual numeric comparison; integers and floats mix freely (`1 <= 1.5`).
- **booleans** with numbers — booleans act as 1 and 0 (`true >= 0` passes).
- **strings** with strings — lexicographic, case-sensitive character-by-character comparison (`"b" > "a"` passes). Note this is *not* numeric: `"10" < "9"`.
- **lists** with lists — element-by-element lexicographic comparison (`[1, 3] > [1, 2]` passes).

Any other combination — a string against a number, `null` against anything — **returns false**, with the underlying comparison error as the message, for example:

```
'>' not supported between instances of 'str' and 'int'
```

This is a failed check (exit 3 under `--fail-on-error`), not a tool error. In particular, an input value of `null` can never pass a comparison.

```json
"condition": { "type": "LessThanEqualTo", "value": 100 }
```

| Input value | Result |
| --- | --- |
| `42` | passes |
| `100` | passes |
| `"42"` | fails — `'<=' not supported between instances of 'str' and 'int'` |
| `null` | fails |

## IsEmpty

Passes when the input value is `null`, an empty string `""`, an empty list `[]`, or an empty dictionary `{}`. `condition.value` is ignored and may be omitted.

Everything else is "not empty" — including `0` and `false`, which fail this check.

```json
"condition": { "type": "IsEmpty" }
```

| Input value | Result |
| --- | --- |
| `null` | passes |
| `""`, `[]`, `{}` | passes |
| `0` | fails |
| `false` | fails |
| `"x"` | fails |

## IsNotEmpty

Passes **only** when the input value is a non-empty string, a non-empty list, or a non-empty dictionary. `condition.value` is ignored and may be omitted.

`IsNotEmpty` is **not** the negation of `IsEmpty`. Numbers and booleans are not strings, lists, or dictionaries, so they fail `IsNotEmpty` — even though they also fail `IsEmpty`. An input value of `5` fails both checks.

```json
"condition": { "type": "IsNotEmpty" }
```

| Input value | Result |
| --- | --- |
| `"x"`, `[1]`, `{"a": 1}` | passes |
| `""`, `[]`, `{}`, `null` | fails |
| `5` | fails (a number is neither empty nor "not empty") |
| `true` | fails |

## RegexMatch

Passes when the regular expression in `condition.value` is found **anywhere** in the input value (search semantics, not full match). Anchor the pattern with `^` and `$` if you need it to match the whole string. Patterns use Python regular expression syntax and are case-sensitive.

Input handling:

- a **string** input is matched directly (multi-line strings included);
- a **list** or **dictionary** input is first converted to its Python string form and the pattern is matched against that text. Note this form uses single quotes — `["a"]` becomes `['a']`, and `{"a": 2}` becomes `{'a': 2}` — not JSON.
- **numbers, booleans, and `null` are never coerced**: the check returns false. An input value of `42` does not match the pattern `"4"`, and `true` does not match `"True"`.

The pattern itself must be a string; a non-string `condition.value` returns false.

An **invalid pattern** does not abort the run: the check returns false and the message carries the regex error, for example `unterminated character set at position 1`. Under `--fail-on-error` this exits 3, like any other failed check.

```json
"condition": { "type": "RegexMatch", "value": "^us-(east|west)-[12]$" }
```

| Input value | Result |
| --- | --- |
| `"us-east-1"` | passes |
| `"eu-central-1"` | fails |
| `42` (against pattern `"4"`) | fails — numbers are not coerced |

## ContainedIn

Asks: **is the input value inside `condition.value`?** The condition value is the container. Which check runs depends on the types of both sides:

| Input value | Condition value | Check |
| --- | --- | --- |
| string | string | substring: passes if the input occurs anywhere in the condition value (`"amp"` is contained in `"example"`) |
| scalar (string, number, boolean, `null`) | list | element membership: passes if the input equals one of the list's elements |
| list | list | **element** membership, not subset: passes only if the whole input list is one *element* of the condition list. `["a", "b"]` is **not** contained in `["a", "b", "c"]`; `["a"]` *is* contained in `[["a"], ["b"]]`. Lists of scalars are sorted on both sides first, so element order does not matter (`[2, 1]` is found in `[[1, 2], [3]]`) |
| dictionary | dictionary | subset: passes if **every** key of the input exists in the condition value with an equal value |
| scalar | dictionary | key membership: passes if the input is one of the dictionary's keys |
| anything else | number, boolean, or `null` — or a non-string input against a string | **unsupported**: returns false with the message `... is an unsupported data type for evaluating against value in 'condition.value'` |

Two quirks to be aware of:

- The common "is this value in the allowed list" use is the *scalar in list* row. If the provider hands you a **list** and you want to check that each element is allowed, extract the elements individually (for example with a `*` wildcard in `key_path`) rather than testing the list itself, which would be an element-membership test.
- In the string-substring and key-in-dictionary forms, a *failing* check reports the message `Not evaluated` (with `passed: false`). The verdict is correct; only the message is unhelpful.

```json
"condition": { "type": "ContainedIn", "value": ["t3.micro", "t3.small"] }
```

| Input value | Result |
| --- | --- |
| `"t3.micro"` | passes |
| `"m5.large"` | fails |
| `["t3.micro"]` | fails — a list is checked as one element, and `["t3.micro"]` is not an element |

## NotContainedIn

Asks: **is the input value absent from `condition.value`?** Broadly the negation of [`ContainedIn`](#containedin), with the same type table — but with two deliberate differences:

- **Dictionaries:** passes if **no** key of the input has an equal value in the condition value. Keys of the input that are absent from the condition value are ignored. This makes the pair asymmetric: with input `{"a": 1, "b": 2}` and condition value `{"a": 1}`, `ContainedIn` fails (key `b` is missing from the container) *and* `NotContainedIn` also fails (key `a` matches). Both directions can fail for the same pair.
- **Unsupported types are still failures, not passes.** If the condition value is a number, boolean, or `null`, `NotContainedIn` returns false with the same "unsupported data type" message that `ContainedIn` produces. A check like `NotContainedIn: null` can never pass.

```json
"condition": { "type": "NotContainedIn", "value": ["0.0.0.0/0", "::/0"] }
```

| Input value | Result |
| --- | --- |
| `"10.0.0.0/16"` | passes |
| `"0.0.0.0/0"` | fails |

## Contains

The mirror image of [`ContainedIn`](#containedin): asks **does the input value contain `condition.value`?** Here the *input* is the container:

| Input value | Condition value | Check |
| --- | --- | --- |
| string | string | substring: passes if the condition value occurs anywhere in the input (`"hello world"` contains `"world"`) |
| list | scalar | element membership |
| list | list | **element** membership, not subset: `["a", "b", "c"]` does not contain `["a", "b"]`, but `[["a"], "b"]` contains `["a"]`. Lists of scalars are sorted on both sides first |
| dictionary | dictionary | subset: passes if every key/value pair of the condition value exists in the input |
| dictionary | scalar | key membership: passes if the condition value is one of the input's keys |
| number, boolean, or `null` input | anything | **unsupported**: returns false with an "unsupported data type" message |

An empty list or empty dictionary input contains nothing, so any search in it fails (except the degenerate `{}` contains `{}`, which passes). Unlike `ContainedIn`, failure messages here are always informative (`Failed to find ... inside ...`).

The practical difference from `ContainedIn`: use `Contains` when the *extracted value* is the collection ("the tags attached to this resource must include X"); use `ContainedIn` when the *policy* holds the collection ("this value must be one of the allowed options").

```json
"condition": { "type": "Contains", "value": {"Environment": "production"} }
```

| Input value | Result |
| --- | --- |
| `{"Environment": "production", "Team": "core"}` | passes |
| `{"Environment": "staging", "Team": "core"}` | fails |
| `null` | fails — unsupported input type |

## NotContains

Asks: **does the input value *not* contain `condition.value`?** Broadly the negation of [`Contains`](#contains), with the same two departures the other `Not*` evaluator has:

- **Dictionaries:** passes if **no** key/value pair of the condition value matches the input. Keys of the condition value that are absent from the input are ignored — `{"z": 1}` is "not contained" in `{"a": 1}` and the check passes.
- **Unsupported input types are failures, not passes.** If the input value is a number, boolean, or `null`, `NotContains` returns false — it does not treat "cannot contain anything" as "does not contain it". An absent (`null`) value therefore fails *both* `Contains` and `NotContains`. (The failure message in this case quotes the condition value rather than the input value.)

```json
"condition": { "type": "NotContains", "value": "0.0.0.0/0" }
```

| Input value | Result |
| --- | --- |
| `["10.0.0.0/16", "192.168.0.0/24"]` | passes |
| `["10.0.0.0/16", "0.0.0.0/0"]` | fails |
| `null` | fails — unsupported input type |

---

## Worked example

Policy (`policy.json`), using the `stackguardian/json` provider:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "region_allowed",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "region"
      },
      "condition": {
        "type": "ContainedIn",
        "value": ["eu-central-1", "eu-west-1"]
      }
    },
    {
      "id": "instances_are_small",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "instances.*.count"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 3
      }
    }
  ],
  "eval_expression": "region_allowed && instances_are_small"
}
```

Input (`input.json`):

```json
{
  "region": "eu-central-1",
  "instances": [
    { "name": "web", "count": 2 },
    { "name": "worker", "count": 5 }
  ]
}
```

Run:

```bash
tirith -policy-path policy.json -input-path input.json
```

`region_allowed` passes. `instances_are_small` receives *two* input values from the wildcard (`2` and `5`); `2 <= 3` passes but `5 <= 3` fails, so the whole evaluator fails and `final_result` is `false`. With `--fail-on-error` the process exits with code 3.

How the per-evaluator verdicts combine into `final_result` is defined by the policy's `eval_expression` — see [Evaluation Expressions](./eval-expressions.md).
