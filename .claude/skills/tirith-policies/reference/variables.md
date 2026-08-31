# Parameterise a policy

One policy, different thresholds per environment, without copying the file.

A variable is referenced as `{{ var.NAME }}`. **The `var.` prefix is required.** A placeholder
written without it — `{{ max_epoch }}` — is not recognised as a variable and is compared as the
literal string, so the check quietly measures the wrong thing instead of failing.

## From a file

```json title="variables.prod.json"
{"max_monthly_cost": 500}
```

```json title="policy.json"
{
  "meta": {"version": "v1", "required_provider": "stackguardian/infracost"},
  "evaluators": [{
    "id": "within_budget",
    "provider_args": {"operation_type": "total_monthly_cost", "resource_type": ["*"]},
    "condition": {"type": "LessThanEqualTo", "value": "{{ var.max_monthly_cost }}"}
  }],
  "eval_expression": "within_budget"
}
```

```bash
tirith -policy-path policy.json -input-path infracost.json \
       -var-path variables.prod.json --fail-on-error
```

`-var-path` may be repeated. Later files override earlier ones on the same key.

## Inline

```bash
tirith -policy-path policy.json -input-path infracost.json \
       -var 'max_monthly_cost=500' --fail-on-error
```

The value is parsed as JSON, so quote strings as JSON strings and pass lists and objects directly:

```bash
-var 'environment="production"'
-var 'allowed_regions=["eu-west-1","eu-central-1"]'
```

## If a variable is not found

The evaluation stops and returns an `errors` entry naming the missing variables, rather than
substituting an empty value and producing a verdict from a policy that was never fully resolved.

## Use it for

- One cost ceiling per environment.
- An allow-list of regions or instance types that differs per team.
- A tag key your organisation renames without editing every policy.

Keep the *shape* of the rule in the policy and only the *values* in variables. A variable that
changes which attribute is read makes the policy unreadable.
