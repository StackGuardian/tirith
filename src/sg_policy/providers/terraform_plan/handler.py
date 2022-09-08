# input->(list ["a.b","c", "d"],value of resource)
# returns->[any, any, any]
import pydash


def _wrapper_get_exp_attribute(attribute, input_resource_change_attrs):
    splitted_attribute = attribute.split(".*.")
    return _get_exp_attribute(splitted_attribute, input_resource_change_attrs)


def _get_exp_attribute(split_expressions, input_data):
    # split_expressions=expression.split('*')
    final_data = []
    for i, expression in enumerate(split_expressions):
        intermediate_val = pydash.get(input_data, expression)
        # print(intermediate_val)
        if isinstance(intermediate_val, list) and i < len(split_expressions) - 1:
            for val in intermediate_val:
                final_attributes = _get_exp_attribute(split_expressions[1:], val)
                for final_attribute in final_attributes:
                    final_data.append(final_attribute)
        elif i == len(split_expressions) - 1 and intermediate_val:
            final_data.append(intermediate_val)
        elif ".*" in expression:
            intermediate_exp = expression.split(".*")
            intermediate_data = pydash.get(input_data, intermediate_exp[0])
            if intermediate_data and isinstance(intermediate_data, list):
                for val in intermediate_data:
                    final_data.append(val)
    return final_data


def provide(provider_inputs, input_data):
    # """Provides the value of the attribute from the input_data"""
    outputs = []
    input_resource_change_attrs = {}
    input_type = provider_inputs["operation_type"]
    resource_changes = input_data["resource_changes"]
    # CASE 1
    # - Get value of an attribute for all instances of a resource
    # - resource_changes.*.change.after.<attr_name>
    if input_type == "attribute":
        attribute = provider_inputs["terraform_resource_attribute"]
        resource_type = provider_inputs["terraform_resource_type"]

        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                input_resource_change_attrs = resource_change["change"]["after"]
                if attribute in input_resource_change_attrs:
                    # attribute key found in the changes
                    outputs.append(
                        {
                            "value": input_resource_change_attrs[attribute],
                            "meta": resource_change,
                            "err": None,
                        }
                    )
                elif "." in attribute or "*" in attribute:
                    evaluated_outputs = _wrapper_get_exp_attribute(attribute, input_resource_change_attrs)
                    for evaluated_output in evaluated_outputs:
                        outputs.append({"value": evaluated_output, "meta": resource_change, "err": None})

        return outputs
    # CASE 2
    # - Get actions performed on a resource
    # - resource_changes.*.change.actions
    elif input_type == "action":
        resource_type = provider_inputs["terraform_resource_type"]
        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                for action in resource_change["change"]["actions"]:
                    outputs.append(
                        {
                            "value": action,
                            "meta": resource_change,
                            "err": None,
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
                resource_meta = resource_change
                count = max(count, resource_change["index"])

        outputs.append(
            {
                "value": count + 1,
                "meta": resource_meta,
                "err": None,
            }
        )
        return outputs
    # CASE 4
    # TODO: Get relationship between resources
    return outputs
