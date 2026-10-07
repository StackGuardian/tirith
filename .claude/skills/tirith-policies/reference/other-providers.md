# Kubernetes, Infracost and JSON

Choosing a provider is choosing what document you have to feed it. Each names the value it reads
with a **different key** — the wrong key is ignored, not rejected, so the evaluator reads nothing
and the check does not measure what you think.

## Kubernetes

`"required_provider": "stackguardian/kubernetes"`, reading YAML or JSON manifests. Multi-document
YAML is supported.

- `operation_type`: `attribute`
- Requires `kubernetes_kind` — `Pod`, `Deployment`, `Service`, …
- Names the value with **`attribute_path`**

```json
{
  "id": "containers_have_liveness_probe",
  "provider_args": {
    "operation_type": "attribute",
    "kubernetes_kind": "Pod",
    "attribute_path": "spec.containers.*.livenessProbe"
  },
  "condition": {"type": "Contains", "value": null, "error_tolerance": 2}
}
```

with `"eval_expression": "!containers_have_liveness_probe"`.

**Why it is written as a detector.** `spec.containers.*.livenessProbe` returns a *list* — one entry
per container, `null` where the probe is missing. `IsNotEmpty` over that list is true as soon as
one container has a probe, which is the wrong question. Test for the presence of `null` and invert.

## Infracost

`"required_provider": "stackguardian/infracost"`, reading an `infracost breakdown --format json`
document.

- `operation_type`: `total_monthly_cost` or `total_hourly_cost`
- `resource_type`: a list. `["*"]` totals everything.

```json
{
  "id": "monthly_cost_ceiling",
  "provider_args": {"operation_type": "total_monthly_cost", "resource_type": ["*"]},
  "condition": {"type": "LessThanEqualTo", "value": 500}
}
```

**The trap: it fails open.** A `resource_type` that matches nothing — a typo, or a type absent from
this plan — sums to `0`, and `0` is less than any ceiling, so the check **passes**. A cost policy
that always passes looks exactly like one that works. Verify against a breakdown that should
exceed the ceiling, and prefer `["*"]` unless you specifically need one type.

## JSON — anything else

`"required_provider": "stackguardian/json"` reads any JSON document: a Terraform state file, an API
response, a CI configuration, a lockfile.

- `operation_type`: `get_value`
- Names the value with **`key_path`**

```json
{
  "id": "approval_required",
  "provider_args": {"operation_type": "get_value", "key_path": "settings.requireApproval"},
  "condition": {"type": "Equals", "value": true}
}
```

`key_path` accepts `*` across a list: `list_of_dicts.*.key1` returns one value per entry, and the
condition is applied to each.

## StackGuardian workflows

`"required_provider": "stackguardian/sg_workflow"` reads a workflow definition, naming the value
with **`workflow_attribute`**, for rules about the pipeline itself rather than the infrastructure —
for example that a Terraform workflow requires approval before apply.

## Jev — a judgment instead of a value

`"required_provider": "stackguardian/jev"` asks the Jev model one question about the document, for
a rule with no attribute to read.

- `operation_type`: `noul` (yes/no, returns a probability from 0 to 1), `choice` (returns the
  chosen option) or `score` (returns a position on a rubric, counted from 0)
- Names the question with **`instructions`**; `choice` and `score` also require `criteria`
- Optional `state_path` (same path syntax as `key_path`), `model`, and `min_confidence` for
  `choice` and `score`

```json
{
  "id": "no_public_exposure",
  "provider_args": {
    "operation_type": "noul",
    "state_path": "resource_changes",
    "instructions": "Does any resource expose a service to the public internet?"
  },
  "condition": {"type": "LessThanEqualTo", "value": 0.2}
}
```

**It is the only provider that calls a network service.** The selected state is sent to
`api.typesafe.ai` and `TYPESAFE_API_KEY` must be set; without the key every check fails. Plans
contain secrets, so set `state_path` rather than sending the whole document. Do not reach for it
when a value can be read directly: a condition over an attribute is deterministic and a model's
answer is not.

Unlike the other providers, an argument it does not read **fails the check** instead of being
ignored, so a mistyped `state_path` cannot send the whole document.

Severities: an answer below `min_confidence` is `1`; a `state_path` that matches nothing, or the
service being unavailable after retries, is `2`. A rejected request or a missing key has no
severity and always fails.
