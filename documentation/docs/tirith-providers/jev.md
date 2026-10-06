---
id: jev-provider
title: Jev Provider
sidebar_label: Jev
description: Reference for the stackguardian/jev provider - the noul, choice and score operations, state selection, confidence, error severities, and the network call it makes.
keywords:
  - tirith
site_name: Tirith
slug: jev-provider/
---

```
required_provider: stackguardian/jev
```

Asks the [Jev](https://docs.typesafe.ai/introduction) model one typed question about the input document and hands the answer to a condition. Use it for a rule that has no attribute to read, such as "does this change expose anything to the public internet?".

:::warning This provider calls a network service
- The selected state is sent to `api.typesafe.ai`. Every other provider reads the input file and nothing else.
- Plans and workflow documents can contain secrets. Use `state_path` to send only what the question needs.
- A verdict is a model's judgment and may differ between runs. Pin `model`, set `min_confidence`, and decide with `error_tolerance` whether an uncertain answer fails or is skipped.
- The document is the model's input, so text inside it can steer the answer. Do not make this provider the only control for a rule that matters when the document's author is not trusted.
:::

## Input document

Any JSON or YAML document. The whole document is the state Jev judges, unless `state_path` selects a part of it.

## Setup

Set `TYPESAFE_API_KEY` in the environment. The key is read from the environment only; it cannot be given in the policy. Without it, every check fails with `TYPESAFE_API_KEY is not set` and no request is sent.

## Operation types

| `operation_type` | Question shape | Value the condition receives |
|---|---|---|
| `noul` | Yes or no | Number from 0 to 1: the probability that the answer is yes |
| `choice` | Which of these options | The chosen option, as a string |
| `score` | Where on this ordered rubric | Number counted from 0, which can fall between levels |

Any other `operation_type` produces an error **without** a severity value, which always fails the check.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `instructions` | yes | The question. |
| `criteria` | `choice`, `score` | `choice`: an object of option to description, 1 to 255 options. `score`: a list of 2 to 10 level descriptions, lowest first. `noul`: optional object with `true` and `false` descriptions. |
| `state_path` | no | Dot-separated path to the part of the input to send, with `*` to iterate, as in the [JSON provider](json.md). Omit it to send the whole document. |
| `model` | no | Model id. Defaults to `jev-latest`. Pin a version such as `jev-1.13.0` so the gate does not change when the alias moves. |
| `min_confidence` | no | Number from 0 to 1, for `choice` and `score`. See [Confidence](#confidence). Rejected on `noul`, which reports no confidence. |

An argument that is not in this table fails the check. Other providers ignore a key they do not read; here a mistyped `state_path` would send the whole document.

### State selection

| `state_path` | State sent |
|---|---|
| omitted | The whole input document |
| matches one value | That value |
| matches several values (with `*`) | The list of matches |
| lands on a number, boolean, null or date | Its JSON text, because Jev accepts a string, an object or an array |
| holds a mapping key JSON cannot carry (a YAML date used as a key), or refers to itself | Nothing is sent; see [Errors](#errors) |
| matches nothing | Nothing is sent; see [Errors](#errors) |

### Reading a `score`

Levels are numbered from 0 in the order you list them. The value is weighted by probability, so three levels can give `1.43`: between the second and third. Compare it with `LessThan`, `GreaterThan` and the inclusive forms rather than `Equals`.

## Confidence

`choice` and `score` answers carry a confidence from 0 to 1. With `min_confidence` set, a less confident answer is not judged: the provider reports a **severity 1** error instead. With the default `error_tolerance` of 0 the check fails; with `error_tolerance: 1` it is skipped. See [error tolerance](../tirith-policies/tirith-policy-error-tolerance.md).

`noul` has no separate confidence. A value near 0.5 is the uncertain one, so choose the threshold in the condition accordingly.

The `meta` of each result that was judged records the model version that answered, the confidence, the full probability distribution, the score legend and the token usage. A result that errored, including one below `min_confidence`, carries only its message.

## Errors

| Situation | Severity | Outcome |
|---|---|---|
| Unsupported `operation_type`, a missing, malformed or unknown parameter, `TYPESAFE_API_KEY` not set, a state JSON cannot carry | none | Always fails |
| The API rejects the request (401, 422, a state over the token limit) | none | Always fails, with the API's message |
| An answer outside the question's terms: a `noul` or a confidence outside 0 to 1, a `score` beyond the rubric, a `choice` that is not one of the options, a response that is not valid JSON or is larger than 1 MiB | none | Always fails |
| Confidence below `min_confidence` | 1 | Fails, or skipped at `error_tolerance: 1` |
| `state_path` matches nothing | 2 | Fails, or skipped at `error_tolerance: 2` |
| Rate limited (429), server error (5xx), timeout or connection failure, after 2 retries | 2 | Fails, or skipped at `error_tolerance: 2` |

So `error_tolerance: 1` skips an uncertain answer and still fails when the service is down. A skipped check is not a pass: if every check is skipped, `final_result` is `null`.

## Limits

- Jev accepts 32k tokens for the state plus the question. A whole Terraform plan is often larger; select a part with `state_path`.
- One request per evaluator. Each attempt waits up to 30 seconds to connect and up to 30 seconds for each read, and a failed attempt is retried up to 2 times.

## In `tirith ui` and `tirith lint`

The Playground evaluates as you type. A policy that names this provider is not sent until you press **Run**. `tirith lint` reports an argument this provider does not accept as an error rather than a warning, because the check will fail.

## Example

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/jev"
  },
  "evaluators": [
    {
      "id": "no_public_exposure",
      "provider_args": {
        "operation_type": "noul",
        "state_path": "resource_changes",
        "instructions": "Does any resource expose a service to the public internet?"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 0.2
      }
    },
    {
      "id": "change_kind",
      "provider_args": {
        "operation_type": "choice",
        "model": "jev-1.13.0",
        "min_confidence": 0.6,
        "instructions": "What kind of change is this?",
        "criteria": {
          "routine": "Config or scaling tweaks",
          "destructive": "Deletes or replaces stateful resources"
        }
      },
      "condition": {
        "type": "Equals",
        "value": "routine",
        "error_tolerance": 1
      }
    },
    {
      "id": "blast_radius",
      "provider_args": {
        "operation_type": "score",
        "instructions": "How much of production could this change take down?",
        "criteria": ["Nothing", "One service", "Several services or shared infrastructure"]
      },
      "condition": {
        "type": "LessThan",
        "value": 1.5
      }
    }
  ],
  "eval_expression": "no_public_exposure && change_kind && blast_radius"
}
```

Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md).
