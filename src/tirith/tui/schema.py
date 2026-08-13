"""
What each provider accepts, declared so a form can be generated from it.

The engine has no machine-readable schema to read this from. `json` and `kubernetes` keep a
`SUPPORTED_OPS` dict, but `terraform_plan` -- the provider almost every real policy uses --
dispatches through an if/elif chain and reads its arguments as bare subscripts
(`provider_inputs["terraform_resource_attribute"]`), and `sg_workflow` has no `operation_type`
at all. There is nothing to introspect, so this table is written by hand.

A hand-written table is a second source of truth, and second sources of truth rot. What stops
that here is tests/tui/test_schema_matches_providers.py, which asserts every provider named
below is really in PROVIDERS_DICT and every operation below is really dispatched by its
handler -- so a provider that gains or renames an operation fails CI rather than silently
leaving the builder able to generate a policy the engine cannot run.

This table is for *generating* and *validating* policies in the TUI. It is deliberately not
imported by the engine: the engine's behaviour is a contract fixed by golden-file tests, and
teaching it to consult a schema would change what it accepts.
"""

from typing import Dict, List, NamedTuple


class Arg(NamedTuple):
    """One provider argument, as a form field."""

    name: str
    required: bool
    help: str
    # Fixed choices where the provider accepts a closed set, else None for free text.
    choices: tuple = ()
    # Rendered as a hint in the form, not as a default that gets written into the policy:
    # writing an unasked-for value into a generated policy is how you get a policy that
    # says something its author did not.
    placeholder: str = ""


class Operation(NamedTuple):
    """One `operation_type` of a provider."""

    name: str
    summary: str
    args: List[Arg]


class Provider(NamedTuple):
    """One provider, as named in a policy's `meta.required_provider`."""

    name: str
    summary: str
    # The document this provider expects as input, for the playground's file picker.
    input_hint: str
    operations: List[Operation]
    # sg_workflow takes `workflow_attribute` and no `operation_type`. Rather than pretend it
    # has one, the flag says so and the builder omits the key entirely.
    uses_operation_type: bool = True


# Shared by several terraform_plan operations.
_RESOURCE_TYPE = Arg(
    "terraform_resource_type",
    True,
    "Resource type to match, or '*' for every type.",
    placeholder="aws_s3_bucket",
)

# infracost takes a *list*, not a string, and `["*"]` is how you ask for the whole plan rather
# than by omitting the key -- `provide` raises KeyError when it is absent. So this is required
# with a wildcard default, where terraform_plan's equivalent is a plain string.
_INFRACOST_RESOURCE_TYPE = Arg(
    "resource_type",
    True,
    'Resource types to sum, as a JSON list. ["*"] totals the whole plan.',
    placeholder='["*"]',
)

PROVIDERS: Dict[str, Provider] = {
    "stackguardian/terraform_plan": Provider(
        name="stackguardian/terraform_plan",
        summary="Query a `terraform show -json` plan: attributes, counts, actions, dependencies.",
        input_hint="terraform plan JSON (terraform show -json tfplan)",
        operations=[
            Operation(
                "attribute",
                "Value of an attribute on every matching resource.",
                [
                    _RESOURCE_TYPE,
                    Arg(
                        "terraform_resource_attribute",
                        True,
                        "Attribute to read from change.after. Supports dots and '*' for nesting.",
                        placeholder="tags.costcenter",
                    ),
                    Arg(
                        "exclude_resource_types",
                        False,
                        "Resource types to skip. Only consulted when the type is '*'.",
                        placeholder='["aws_iam_policy"]',
                    ),
                ],
            ),
            Operation(
                "count",
                "How many resources of a type the plan changes.",
                [_RESOURCE_TYPE],
            ),
            Operation(
                "action",
                "The planned actions (create / update / delete / no-op) per resource.",
                [_RESOURCE_TYPE],
            ),
            Operation(
                "direct_dependencies",
                "Resource types a resource declares in `depends_on`.",
                [_RESOURCE_TYPE],
            ),
            Operation(
                "direct_references",
                "Resources referenced by, or referencing, a resource type.",
                [
                    _RESOURCE_TYPE,
                    Arg(
                        "references_to",
                        False,
                        "Match resources this type points at. Pair with the type above.",
                        placeholder="aws_s3_bucket",
                    ),
                    Arg(
                        "referenced_by",
                        False,
                        "Match resources that point at this type instead.",
                        placeholder="aws_elb",
                    ),
                ],
            ),
            Operation(
                "terraform_version",
                "The terraform version recorded in the plan.",
                [],
            ),
            Operation(
                "provider_config",
                "An attribute of a configured provider, such as its region or version constraint.",
                [
                    Arg(
                        "terraform_provider_full_name",
                        True,
                        "Fully qualified provider name.",
                        placeholder="registry.terraform.io/hashicorp/aws",
                    ),
                    Arg(
                        "attribute",
                        True,
                        "Which provider attribute to read.",
                        choices=("version_constraint", "region"),
                    ),
                ],
            ),
        ],
    ),
    "stackguardian/json": Provider(
        name="stackguardian/json",
        summary="Read any path out of an arbitrary JSON or YAML document.",
        input_hint="any JSON or YAML document",
        operations=[
            Operation(
                "get_value",
                "Value(s) at a dotted path. '*' matches every element of a list.",
                [
                    Arg(
                        "key_path",
                        True,
                        "Dotted path into the document. '*' walks every item of a list.",
                        placeholder="spec.containers.*.image",
                    )
                ],
            )
        ],
    ),
    "stackguardian/kubernetes": Provider(
        name="stackguardian/kubernetes",
        summary="Read a path out of Kubernetes manifests, including multi-document YAML.",
        input_hint="Kubernetes manifest YAML or JSON",
        operations=[
            Operation(
                "attribute",
                "Value(s) at a dotted path within manifests of one kind.",
                [
                    Arg(
                        "kubernetes_kind",
                        True,
                        "Manifest kind to match. Documents of other kinds are ignored.",
                        placeholder="Pod",
                    ),
                    # Named attribute_path here, key_path in the json provider. The two
                    # providers really do disagree; do not "fix" one to match the other.
                    Arg(
                        "attribute_path",
                        True,
                        "Dotted path into the manifest. '*' walks every item of a list.",
                        placeholder="spec.containers.*.livenessProbe",
                    ),
                ],
            )
        ],
    ),
    "stackguardian/infracost": Provider(
        name="stackguardian/infracost",
        summary="Read costs out of an `infracost breakdown --format json` report.",
        input_hint="infracost breakdown JSON",
        operations=[
            Operation(
                "total_monthly_cost",
                "Monthly cost, summed across the named resource types.",
                [_INFRACOST_RESOURCE_TYPE],
            ),
            Operation(
                "total_hourly_cost",
                "Hourly cost, summed across the named resource types.",
                [_INFRACOST_RESOURCE_TYPE],
            ),
        ],
    ),
    "stackguardian/sg_workflow": Provider(
        name="stackguardian/sg_workflow",
        summary="Read a field off a StackGuardian workflow definition.",
        input_hint="StackGuardian workflow JSON",
        uses_operation_type=False,
        operations=[
            Operation(
                "workflow_attribute",
                "A named field of the workflow.",
                [
                    Arg(
                        "workflow_attribute",
                        True,
                        "Which workflow field to read.",
                        # Exactly the keys __getValue branches on. Anything else raises
                        # KeyError inside the provider, so the closed list is the point.
                        choices=(
                            "Description",
                            "DocVersion",
                            "ResourceName",
                            "ResourceType",
                            "Tags",
                            "WfType",
                            "approvalPreApply",
                            "driftCheck",
                            "managedTerraformState",
                            "terraformVersion",
                            "integrationId",
                            "iacTemplateId",
                            "useMarketplaceTemplate",
                            "bucket_region",
                            "s3_bucket_acl",
                            "s3_bucket_block_public_acls",
                            "s3_bucket_block_public_policy",
                            "s3_bucket_force_destroy",
                            "s3_bucket_ignore_public_acls",
                            "s3_bucket_restrict_public_buckets",
                        ),
                    )
                ],
            )
        ],
    ),
}


class EvaluatorInfo(NamedTuple):
    name: str
    summary: str
    # What `condition.value` should look like, to steer the form's input widget.
    value_kind: str  # "scalar" | "list" | "none" | "regex"


# Mirrors EVALUATORS_DICT; the drift-guard test asserts the two agree.
EVALUATORS: Dict[str, EvaluatorInfo] = {
    "Equals": EvaluatorInfo("Equals", "Value is exactly this.", "scalar"),
    "NotEquals": EvaluatorInfo("NotEquals", "Value is anything but this.", "scalar"),
    "GreaterThan": EvaluatorInfo("GreaterThan", "Value is strictly greater.", "scalar"),
    "GreaterThanEqualTo": EvaluatorInfo("GreaterThanEqualTo", "Value is greater or equal.", "scalar"),
    "LessThan": EvaluatorInfo("LessThan", "Value is strictly less.", "scalar"),
    "LessThanEqualTo": EvaluatorInfo("LessThanEqualTo", "Value is less or equal.", "scalar"),
    "Contains": EvaluatorInfo("Contains", "Value contains this item or substring.", "scalar"),
    "NotContains": EvaluatorInfo("NotContains", "Value does not contain this.", "scalar"),
    "ContainedIn": EvaluatorInfo("ContainedIn", "Value is one of these.", "list"),
    "NotContainedIn": EvaluatorInfo("NotContainedIn", "Value is none of these.", "list"),
    "IsEmpty": EvaluatorInfo("IsEmpty", "Value is empty.", "none"),
    "IsNotEmpty": EvaluatorInfo("IsNotEmpty", "Value is not empty.", "none"),
    "RegexMatch": EvaluatorInfo("RegexMatch", "Value matches this regular expression.", "regex"),
}


# What the Builder opens on. Not the alphabetically-first provider, which is infracost: the
# terraform plan is what nearly every policy targets, so it is the representative starting
# point for someone learning the form.
DEFAULT_PROVIDER = "stackguardian/terraform_plan"


def provider_names() -> List[str]:
    return sorted(PROVIDERS)


def evaluator_names() -> List[str]:
    return sorted(EVALUATORS)


def operations_for(provider_name: str) -> List[Operation]:
    provider = PROVIDERS.get(provider_name)
    return list(provider.operations) if provider else []


def operation_for(provider_name: str, operation_name: str):
    for operation in operations_for(provider_name):
        if operation.name == operation_name:
            return operation
    return None
