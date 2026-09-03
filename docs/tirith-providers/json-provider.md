# JSON Provider

Source: https://stackguardian.github.io/tirith/docs/tirith-providers/json-provider/
Summary: Reference for the stackguardian/json provider - the get_value operation, key path syntax, return shapes, and error behavior.

```
required_provider: stackguardian/json
```

Extracts values from any JSON or YAML document by key path. Use this provider when no specialized provider exists for your input format.

## Input document

Any JSON file, or any YAML file (`.yaml` / `.yml` extension). A YAML file with multiple documents (separated by `---`) is parsed into a **list** of documents; start the key path with `*.` to iterate over them.

## Operation types

| `operation_type` | Purpose |
|---|---|
| `get_value` | Get the value(s) at a key path |

Any other `operation_type` produces an error **without** a severity value, which always fails the check.

---

## `get_value`

| Parameter | Required | Description |
|---|---|---|
| `key_path` | yes | Dot-separated path into the document. `*` as a path segment iterates over every element of a list or every value of a dict. |

Path syntax, with examples of what each returns:

| `key_path` | Input | Values produced |
|---|---|---|
| `a.b` | `{"a": {"b": 1}}` | `1` |
| `c` | `{"c": ["aa", "bb"]}` | `["aa", "bb"]` (the whole list, one value) |
| `nested_map` | `{"nested_map": {"e": {"f": "3"}}}` | `{"e": {"f": "3"}}` (the whole dict, one value) |
| `list_of_dict.*.key1` | `{"list_of_dict": [{"key1": "value1"}, {"key1": "value1"}]}` | `"value1"`, `"value1"` (one value per element) |
| `countries.*.capital` | `{"countries": {"US": {"capital": "Washington"}, "UK": {"capital": "London"}}}` | `"Washington"`, `"London"` (one per dict value) |
| `*.name` | `[{"name": "Alice"}, {"name": "Bob"}]` | `"Alice"`, `"Bob"` (leading `*` over a top-level list) |

**Returns:** one result per value found at the path. Without `*`, that is a single value of whatever shape lives there (scalar, list, or dict). With `*`, one result per matched element — and the condition must pass for **every** one of them.

**On a miss:** if the path matches nothing, the provider reports an error with **severity 2** (`` key_path: `...` is not found ``). With the default `error_tolerance` of 0 the check fails; with `error_tolerance: 2` it is skipped instead. See [error tolerance](../tirith-policies/tirith-policy-error-tolerance.md).

## Examples

Verified end-to-end against the test fixtures:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "check0",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "z.b"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 1,
        "error_tolerance": 2
      }
    },
    {
      "id": "check1",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "a.b"
      },
      "condition": {
        "type": "LessThanEqualTo",
        "value": 1
      }
    },
    {
      "id": "check2",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "c"
      },
      "condition": {
        "type": "Contains",
        "value": "aa"
      }
    },
    {
      "id": "check4",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "list_of_dict.*.key1"
      },
      "condition": {
        "type": "Equals",
        "value": "value1"
      }
    }
  ],
  "eval_expression": "check1 && check2 && check4"
}
```

(`check0` targets a path that does not exist; with `error_tolerance: 2` it is skipped and dropped from `eval_expression` instead of failing.)

The provider also works on YAML — this policy checks an Ansible playbook (a YAML file whose top level is a list of plays, hence the leading `*.`):

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "check0",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "*.vars.region"
      },
      "condition": {
        "type": "Equals",
        "value": "your_aws_region"
      }
    }
  ],
  "eval_expression": "check0"
}
```

Condition types are documented in the [evaluators reference](../tirith-reference/evaluators.md).
