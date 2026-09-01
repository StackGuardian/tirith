# Policy Structure

Source: https://stackguardian.github.io/tirith/docs/tirith-policies/tirith-policy-structure/
Summary: Learn about the structure of Tirith policies, including metadata, evaluators, and evaluation expressions.

Tirith policies are written in JSON format, following a structured approach that defines rules and conditions for evaluating input data. Each policy consists of:

- **Metadata** (`meta`): Specifies the policy version and required provider.
- **Evaluators** (`evaluators`): A list of conditions that determine if the input meets the policy requirements.
- **Evaluation Expression** (`eval_expression`): Defines how evaluators are combined to determine the final result.

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "can_post",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "verb"
      },
      "condition": {
        "type": "Equals",
        "value": "POST"
      }
    }
  ],
  "eval_expression": "can_post"
}
```
