"""
terraform_plan provider

Error severity values explanation
Value = 1, When a resource is not found
Value = 2, When an attribute of a resource is not found
"""
# input->(list ["a.b","c", "d"],value of resource)
# returns->[any, any, any]
import pydash

from ..common import ProviderError


class PydashPathNotFound:
    pass


def _wrapper_get_exp_attribute(attribute, input_resource_change_attrs):
    splitted_attribute = attribute.split(".*.")
    return _get_exp_attribute(splitted_attribute, input_resource_change_attrs)


def _get_exp_attribute(split_expressions, input_data):
    # split_expressions=expression.split('*')
    final_data = []
    for i, expression in enumerate(split_expressions):
        intermediate_val = pydash.get(input_data, expression, default=PydashPathNotFound)
        if isinstance(intermediate_val, list) and i < len(split_expressions) - 1:
            for val in intermediate_val:
                final_attributes = _get_exp_attribute(split_expressions[1:], val)
                for final_attribute in final_attributes:
                    final_data.append(final_attribute)
        elif i == len(split_expressions) - 1 and intermediate_val is not PydashPathNotFound:
            final_data.append(intermediate_val)
        elif ".*" in expression:
            intermediate_exp = expression.split(".*")
            intermediate_data = pydash.get(input_data, intermediate_exp[0], default=PydashPathNotFound)
            if intermediate_data is not PydashPathNotFound and isinstance(intermediate_data, list):
                for val in intermediate_data:
                    final_data.append(val)
    return final_data


def provide(provider_inputs, input_data):
    # """Provides the value of the attribute from the input_data"""
    outputs = []
    input_resource_change_attrs = {}
    input_type = provider_inputs["operation_type"]
    resource_changes = input_data.get("resource_changes")
    if not resource_changes:
        outputs.append(
            {
                "value": ProviderError(severity_value=0),
                "err": f"No Terraform resources changes are found",
            }
        )
        return outputs
    # CASE 1
    # - Get value of an attribute for all instances of a resource
    # - resource_changes.*.change.after.<attr_name>
    if input_type == "attribute":
        attribute = provider_inputs["terraform_resource_attribute"]
        resource_type = provider_inputs["terraform_resource_type"]

        is_resource_found = False
        is_attribute_found = False

        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                is_resource_found = True
                input_resource_change_attrs = resource_change["change"]["after"]
                if input_resource_change_attrs:
                    if attribute in input_resource_change_attrs:
                        is_attribute_found = True
                        outputs.append(
                            {
                                "value": input_resource_change_attrs[attribute],
                                "meta": resource_change,
                                "err": None,
                            }
                        )
                    elif "." in attribute or "*" in attribute:
                        evaluated_outputs = _wrapper_get_exp_attribute(attribute, input_resource_change_attrs)
                        if evaluated_outputs:
                            is_attribute_found = True
                        for evaluated_output in evaluated_outputs:
                            outputs.append({"value": evaluated_output, "meta": resource_change, "err": None})
                else:
                    outputs.append(
                        {
                            "value": ProviderError(severity_value=0),
                            "err": f"No Terraform changes found for resource type: '{resource_type}'",
                        }
                    )
        if not outputs:
            if not is_resource_found:
                outputs.append(
                    {
                        "value": ProviderError(severity_value=1),
                        "err": f"resource_type: '{resource_type}' is not found",
                    }
                )
                return outputs
            if not is_attribute_found:
                outputs.append(
                    {
                        "value": ProviderError(severity_value=2),
                        "err": f"attribute: '{attribute}' is not found",
                    }
                )

        return outputs
    # CASE 2
    # - Get actions performed on a resource
    # - resource_changes.*.change.actions
    elif input_type == "action":
        resource_type = provider_inputs["terraform_resource_type"]
        is_resource_type_found = False
        for resource_change in resource_changes:
            if resource_type in (resource_change["type"], "*"):
                is_resource_type_found = True
                for action in resource_change["change"]["actions"]:
                    outputs.append(
                        {
                            "value": action,
                            "meta": resource_change,
                            "err": None,
                        }
                    )
        if not is_resource_type_found:
            outputs.append(
                {
                    "value": ProviderError(severity_value=1),
                    "err": f"resource_type: '{resource_type}' is not found",
                }
            )
        return outputs
    # CASE 3
    # - Get count of a particular resource
    # - resource_changes.*.index
    elif input_type == "count":
        count = 0
        resource_meta = {}
        resource_type = provider_inputs["terraform_resource_type"]
        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                # No need to check if the resource is not found
                # because the count of a resource can be zero
                resource_meta = resource_change
                count = +1

        outputs.append(
            {
                "value": count,
                "meta": resource_meta,
                "err": None,
            }
        )
        return outputs
    # CASE 4
    elif input_type == "direct_dependencies":
        direct_dependencies_operator(input_data, provider_inputs, outputs)
    elif input_type == "direct_references":
        direct_references_operator(input_data, provider_inputs, outputs)
    else:
        outputs.append(
            {
                "value": ProviderError(severity_value=99),
                "err": f"operation_type: '{input_type}' is not supported (severity_value: 99)",
            }
        )
    return outputs


def direct_dependencies_operator(input_data: dict, provider_inputs: dict, outputs: list):
    config_resources = input_data.get("configuration", {}).get("root_module", {}).get("resources", [])
    resource_type = provider_inputs.get("terraform_resource_type")

    if not resource_type:
        outputs.append(
            {
                "value": ProviderError(severity_value=99),
                "err": "`terraform_resource_type` must be provided in the provider input (severity_value: 99))",
            }
        )
        return

    is_resource_found = False

    for resource in config_resources:
        if resource.get("type") != resource_type:
            continue
        is_resource_found = True
        deps_resource_type = {resource_id.split(".")[0] for resource_id in resource.get("depends_on", [])}
        outputs.append({"value": list(deps_resource_type), "meta": config_resources})

    if not is_resource_found:
        outputs.append(
            {
                "value": ProviderError(severity_value=1),
                "err": f"resource_type: '{resource_type}' is not found",
                "meta": config_resources,
            }
        )


def direct_references_operator_referenced_by(input_data: dict, provider_inputs: dict, outputs: list):
    # Verify that all of the terraform_resource_type instances are
    # referenced by `referenced_by`
    # Idea:
    # - Get all of the resource_type instances id save it in a list
    # - Iterate through all of the referenced_by instances, read what it references to,
    #   check if it is in the list of resource_type instances, if it is, pop the element
    # - If the list is empty, then all of the resource_type instances are
    #   referenced by `referenced_by` return true, otherwise false
    config_resources = input_data.get("configuration", {}).get("root_module", {}).get("resources", [])
    resource_type = provider_inputs.get("terraform_resource_type")
    resource_changes = input_data.get("resource_changes", [])
    referenced_by = provider_inputs.get("referenced_by")

    reference_target_addresses = set()
    is_resource_found = False

    # Loop for adding reference_target
    for resource_change in resource_changes:
        if resource_change.get("type") != resource_type or resource_change.get("change", {}).get("actions") == [
            "destroy"
        ]:
            continue
        reference_target_addresses.add(resource_change.get("address"))
        is_resource_found = True

    if not is_resource_found:
        outputs.append(
            {
                "value": ProviderError(severity_value=1),
                "err": f"resource_type: '{resource_type}' is not found (severity_value: 1)",
                "meta": config_resources,
            }
        )
        return

    # Loop for removing reference_target
    for resource_change in resource_changes:
        if resource_change.get("type") != referenced_by:
            continue

        # Look to the resource_config to get the references
        for resource_config in get_resource_config_by_type(input_data, referenced_by):
            for expression_val_dict in resource_config.get("expressions", {}).values():
                if not isinstance(expression_val_dict, dict):
                    continue

                for reference_address in expression_val_dict.get("references", []):
                    if reference_address in reference_target_addresses:
                        reference_target_addresses.remove(reference_address)

    is_all_referenced = len(reference_target_addresses) == 0
    outputs.append({"value": is_all_referenced, "meta": config_resources})


def get_resource_config_by_type(input_data: dict, resource_type: str) -> iter:
    """
    Get all of the resource config by type

    :param input_data:    The input data
    :param resource_type: The resource type
    :return:              The resource config (iterable)
    """
    config_resources = input_data.get("configuration", {}).get("root_module", {}).get("resources", [])

    for config_resource in config_resources:
        if config_resource.get("type") != resource_type:
            continue
        yield config_resource


def direct_references_operator_references_to(input_data: dict, provider_inputs: dict, outputs: list):
    # The exact opposite of `direct_references_operator_referenced_by`
    config_resources = input_data.get("configuration", {}).get("root_module", {}).get("resources", [])
    resource_changes = input_data.get("resource_changes", [])
    resource_type = provider_inputs.get("terraform_resource_type")
    references_to_type = provider_inputs.get("references_to")

    resource_type_count = 0
    reference_count = 0
    is_resource_found = False

    for resource_change in resource_changes:
        if resource_change.get("type") != resource_type or resource_change.get("change", {}).get("actions") == [
            "destroy"
        ]:
            continue
        is_resource_found = True
        resource_type_count += 1
        resource_change_address = resource_change.get("address")

        # Look to the resource_config to get the references
        for resource_config in get_resource_config_by_type(input_data, resource_type):
            if resource_config.get("address") != resource_change_address:
                continue
            for expression_val_dict in resource_config.get("expressions", {}).values():
                if not isinstance(expression_val_dict, dict):
                    continue
                for reference in expression_val_dict.get("references", []):
                    reference_res_type = reference.split(".")[0]
                    if reference_res_type == references_to_type:
                        reference_count += 1
                        # We break early because most of the times the references
                        # list contains something like this:
                        # ["aws_s3_bucket.a.id", "aws_s3_bucket.a"]
                        break

    if not is_resource_found:
        outputs.append(
            {
                "value": ProviderError(severity_value=1),
                "err": f"resource_type: '{resource_type}' is not found (severity_value: 1)",
                "meta": config_resources,
            }
        )
        return

    is_all_resource_type_references_to = resource_type_count == reference_count
    outputs.append({"value": is_all_resource_type_references_to, "meta": config_resources})


def direct_references_operator(input_data: dict, provider_inputs: dict, outputs: list):
    referenced_by = provider_inputs.get("referenced_by")
    references_to = provider_inputs.get("references_to")

    if referenced_by is not None and references_to is not None:
        outputs.append(
            {
                "value": ProviderError(severity_value=99),
                "err": "Only one of `referenced_by` or `references_to` must be provided in the provider input (severity_value: 99))",
            }
        )
        return

    if referenced_by is not None:
        return direct_references_operator_referenced_by(input_data, provider_inputs, outputs)

    if references_to is not None:
        return direct_references_operator_references_to(input_data, provider_inputs, outputs)

    config_resources = input_data.get("configuration", {}).get("root_module", {}).get("resources", [])
    resource_type = provider_inputs.get("terraform_resource_type")

    if not resource_type:
        outputs.append(
            {
                "value": ProviderError(severity_value=99),
                "err": "`terraform_resource_type` must be provided in the provider input (severity_value: 99))",
            }
        )
        return

    is_resource_found = False

    for resource in config_resources:
        if resource.get("type") != resource_type:
            continue
        is_resource_found = True
        resource_references = set()
        for expressions_val in resource.get("expressions", {}).values():
            # Currently we don't support expressions other than dict
            # Might be needed in the future to search references in lists
            # Ideally we should do `*.references`
            if not isinstance(expressions_val, dict):
                continue
            for reference in expressions_val.get("references", []):
                # Only get the resource type
                resource_references.add(reference.split(".")[0])

        outputs.append({"value": list(resource_references), "meta": resource})

    if not is_resource_found:
        outputs.append(
            {
                "value": ProviderError(severity_value=1),
                "err": f"resource_type: '{resource_type}' is not found (severity_value: 1)",
                "meta": config_resources,
            }
        )
