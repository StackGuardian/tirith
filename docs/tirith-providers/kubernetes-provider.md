# Kubernetes Provider

Source: https://stackguardian.github.io/tirith/docs/tirith-providers/kubernetes-provider/
Summary: Reference for the stackguardian/kubernetes provider - the attribute operation, parameters, return shapes, and error behavior.

```
required_provider: stackguardian/kubernetes
```

Extracts attribute values from Kubernetes manifests of a chosen `kind` (Pod, Deployment, Service, ...).

## Input document

A **list** of Kubernetes manifests. In practice this is a multi-document YAML file — for example the output of `helm template` or a concatenation of manifests separated by `---`:

```bash
helm template my-release ./chart > manifests.yml
tirith -policy-path policy.json -input-path manifests.yml
```

Every document in the list must have a `kind` key. Note that a YAML file containing only a **single** document does not currently work with this provider — the input must parse to a list of manifests (two or more YAML documents, or a JSON array).

## Operation types

| `operation_type` | Purpose |
|---|---|
| `attribute` | Get the value at an attribute path from every manifest of a kind |

Any other `operation_type` produces an error **without** a severity value, which always fails the check.

---

## `attribute`

| Parameter | Required | Description |
|---|---|---|
| `kubernetes_kind` | yes | The `kind` to match, e.g. `Pod`, `Deployment`. Exact match. Omitting it produces a severity 99 error. |
| `attribute_path` | yes | Dot-separated path into the manifest, e.g. `spec.containers.*.image`. `*` as a path segment iterates over every element of a list or every value of a dict. Omitting it (or passing an empty string) produces a severity 99 error. |

**Returns:** one result per manifest whose `kind` matches:

- If `attribute_path` contains **no** `*` — the single value at that path (scalar, list, or dict), or `null` when the path is absent from that manifest.
- If `attribute_path` contains `*` — a **list** with one entry per matched element; elements where the remainder of the path is absent appear as `null` in the list. The condition is applied to the list as a whole, which makes `Contains` / `NotContains` (checking for `null` entries) the natural conditions to pair with wildcard paths.

**On a miss:** no manifest of the requested kind — severity 1 (`kind: ... is not found`). A present kind with an absent path is **not** an error; it produces `null` values as described above.

## Example

Verified end-to-end against the test fixtures — every container of every `Pod` must define a `livenessProbe`:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/kubernetes"
  },
  "evaluators": [
    {
      "id": "kinds_have_null_liveness_probe",
      "provider_args": {
        "operation_type": "attribute",
        "kubernetes_kind": "Pod",
        "attribute_path": "spec.containers.*.livenessProbe"
      },
      "condition": {
        "type": "Contains",
        "value": null,
        "error_tolerance": 2
      }
    }
  ],
  "eval_expression": "!kinds_have_null_liveness_probe"
}
```

How this works: for each `Pod`, the provider returns the list of every container's `livenessProbe` value, with `null` for containers that lack one. The `Contains: null` condition is true when at least one container is missing the probe, and the `eval_expression` negates it, so the policy passes only when every container defines a probe.

Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md).
