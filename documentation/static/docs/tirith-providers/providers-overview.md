# Providers Overview

Source: https://stackguardian.github.io/tirith/docs/tirith-providers/providers-overview/
Summary: What a Tirith provider is, how required_provider selects one, how provider_args are passed, and the list of available providers.

A **provider** is the part of Tirith that knows how to read one specific kind of input document and extract values from it. The policy declares which provider to use; each evaluator in the policy then asks the provider for values (via `provider_args`), and the evaluator's `condition` is applied to every value the provider returns.

## Selecting a provider

The provider is selected once for the whole policy with `meta.required_provider`:

```json
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan"
  },
  "evaluators": [ ... ],
  "eval_expression": "..."
}
```

The value must be one of the exact strings below. If the string does not match any known provider, every evaluator in the policy fails with an error.

| `required_provider` | Summary | Expected input document |
|---|---|---|
| [`stackguardian/terraform_plan`](terraform-plan.md) | Inspects resource changes, actions, counts, dependencies, references, provider configuration, and the Terraform version in a Terraform plan. | Terraform plan in JSON form (`terraform show -json <plan-file>`) |
| [`stackguardian/infracost`](infracost.md) | Sums estimated monthly or hourly costs from an Infracost breakdown. | Infracost output (`infracost breakdown --format json`) |
| [`stackguardian/json`](json.md) | Extracts values from any JSON or YAML document by key path, with wildcard support. | Any JSON or YAML file |
| [`stackguardian/kubernetes`](kubernetes.md) | Extracts attribute values from Kubernetes manifests of a given `kind`. | A list of Kubernetes manifests (multi-document YAML, e.g. `helm template` output) |
| [`stackguardian/sg_workflow`](sg-workflow.md) | Reads attributes of a StackGuardian workflow definition. | StackGuardian workflow JSON |

## How `provider_args` reaches the provider

Each evaluator carries a `provider_args` object. Tirith hands that object to the selected provider **verbatim** — the provider decides which keys it understands. Every provider except `stackguardian/sg_workflow` dispatches on the `operation_type` key; the remaining keys are parameters of that operation.

```json
{
  "id": "my_check",
  "provider_args": {
    "operation_type": "attribute",
    "terraform_resource_type": "aws_s3_bucket",
    "terraform_resource_attribute": "force_destroy"
  },
  "condition": {
    "type": "Equals",
    "value": false
  }
}
```

The provider returns a **list of results**. Each result is a value extracted from the input (a scalar, a list, or a dict, depending on the operation). The evaluator's `condition` is applied to each value independently, and the evaluator passes only if **every** value passes. If the provider returns nothing at all, the evaluator fails with the message `Could not find input value`.

For the available condition types (`Equals`, `Contains`, `RegexMatch`, ...) see the [evaluators reference](../tirith-reference/evaluators.md).

## How the input document is parsed

The file given to [`-input-path`](../tirith-usage/cli-reference.md) is parsed by extension:

- `.yaml` / `.yml` — parsed as YAML. A file with multiple documents (separated by `---`) becomes a **list** of documents; a file with a single document becomes that document directly.
- anything else — parsed as JSON.

The parsed value is what the provider sees.

## Errors, misses, and `error_tolerance`

When a provider cannot find what an operation asked for, it reports an error instead of a value. There are two kinds:

1. **Errors with a severity value.** Most "not found" situations carry a numeric severity. Whether the check fails or is skipped depends on the evaluator's `condition.error_tolerance` (default `0`):
   - severity **greater than** `error_tolerance` — the check **fails**.
   - severity **less than or equal to** `error_tolerance` — the check is **skipped** (its `passed` is `null`, and its id is dropped from `eval_expression`).

   The conventional severity values are:

   | Severity | Meaning |
   |---|---|
   | 0 | Nothing to inspect (e.g. no resource changes in the plan). Skipped even at the default tolerance. |
   | 1 | The requested resource / kind / provider was not found. |
   | 2 | The resource was found but the requested attribute / key path was not. |
   | 99 | The `provider_args` themselves are invalid (unsupported operation, missing required parameter). Practically never tolerated. |

2. **Errors without a severity value.** Some errors (an unsupported `operation_type` in the `json` and `kubernetes` providers, and all errors from the `infracost` and `sg_workflow` providers) carry no severity. These always **fail** the check, regardless of `error_tolerance`.

Each provider page below lists exactly which situation produces which severity. See also [error tolerance](../tirith-policies/tirith-policy-error-tolerance.md).

## Write one for what you actually run

Five providers ship. That is not a claim about what is worth gating, it is a list of what has been written so far, and the interesting policies are usually about the system nobody wrote a provider for yet.

A provider is small. It is one function:

```python
def provide(provider_args: dict, input_data) -> list[dict]:
    """Turn a document into values a condition can be run against."""
```

It receives the `provider_args` from an evaluator and the parsed input document, and it returns a list of outputs: `{"value": ...}` for something a condition can judge, or `{"value": ProviderError(severity_value=1), "err": "..."}` for something it could not find. That is the entire contract. The thirteen conditions, `eval_expression`, `error_tolerance`, the result document, the exit codes and every CI integration already work on top of it. `kubernetes/handler.py` is about fifty lines, and it is a complete provider.

[NOTE] How a provider is registered
There is no plugin discovery and no entry point to hook: `PROVIDERS_DICT` in `src/tirith/providers/__init__.py` is a literal dictionary, so a new provider is a module plus one line in that dict. In practice that means a pull request, or a fork you install from your own git URL. Making providers loadable from outside the package is a real request and worth opening an issue for if you need it.

### What people ask for

The pattern that makes a good provider is narrow: **a document that describes a proposed change, available before the change is applied.** If you can get that as JSON, you can gate it.

| | |
|---|---|
| **Other IaC formats** | CloudFormation change sets, Pulumi previews, ARM and Bicep what-if output, Helm rendered templates and values |
| **Cloud and SaaS APIs** | AWS Config or Cloud Control, GCP asset inventory, Datadog monitors, PagerDuty schedules, an identity provider's roles |
| **Your own APIs** | A service catalogue, a CMDB, a deployment API, an internal platform's change request. This is the one nobody else can write for you, and it is usually where the rules that matter to your organisation live |
| **Supply chain** | An SBOM, a lockfile, a dependency manifest, image provenance and signatures |
| **Cost and capacity** | Beyond Infracost: quota headroom, commitment coverage, a chargeback model |
| **Compliance evidence** | Turning a control framework into checks that run on every change instead of once a quarter |

### The one that does not exist yet

Everything above is the same shape as what ships today: a plan, a manifest, an estimate. The shape holds somewhere less obvious.

An AI agent with tools is a system that proposes changes and then applies them. Before it calls a tool, there is a document describing what it is about to do: which tool, which arguments, what it costs, what it can reach. That is a plan, in every sense that matters to a policy engine, and today almost nothing sits between an agent's intention and its action.

**A provider for agent runtime decisions** would let the rules be written the same way the rest of your governance is: this agent may not call a tool that writes to production, may not spend beyond a threshold in one run, may not touch a resource outside its blast radius, may not act at all without a plan a human approved. The same thirteen conditions, the same expression grammar, the same verdict and exit code, evaluated before the call rather than in a review afterwards.

This is **aspirational**. There is no such provider, it is not on the [roadmap](https://stackguardian.github.io/tirith/roadmap/) with a date, and it is written down here because it is the clearest example of the point: the engine does not care what the document is about. If you are building agent infrastructure and want a policy layer with a real evaluator behind it rather than a prompt asking a model to behave, this is worth a conversation.

### Start one

Open an issue describing the document you want to gate and what a rule over it would say. That is enough to work out whether it is a new provider, a new operation on an existing one, or something the `json` provider already does.

- **[Propose a provider](https://github.com/StackGuardian/tirith/issues/new?template=feature_request.md&title=Provider%3A+)**: the system, the document, and one rule you would write
- **[Read an existing one](https://github.com/StackGuardian/tirith/tree/main/src/tirith/providers/kubernetes)**: the shortest complete example in the repository
- **[Good first issues](https://github.com/StackGuardian/tirith/labels/good%20first%20issue)**: if you would rather start somewhere smaller
