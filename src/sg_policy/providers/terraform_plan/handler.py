import logging

# TODO: Add at least __name__ as the name of the logger
logger = logging.getLogger()

# input->(list [s3,acl,*],value of resource)
# returns->[any, any, any]

def __get_expression_attribute(splitted_attr_name_expr, input_data):

    if not splitted_attr_name_expr:
        return input_data

    lookup_key = splitted_attr_name_expr[0]

    if lookup_key != "*":
        print("lookup key    -", lookup_key)
        print("input_data    -", input_data)
        if type(input_data) == dict:
            input_data_new = input_data[lookup_key]
        elif type(input_data) == list:
            print(input_data)
            if type(input_data[0]) == list:

                input_data_new = input_data[0][0][lookup_key]
            else:
                input_data_new = input_data[0][lookup_key]
            print(input_data_new)

        else:
            input_data_new = input_data[lookup_key]

        # print("input_new    -",input_data_new)

        _get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)

    elif lookup_key == "*" and isinstance(input_data, list):
        print("lookup key    -", lookup_key)
        print("input_data    -", input_data)
        values = []
        lookup_key = splitted_attr_name_expr[1:2][0]
        splitted_attr_name_expr = splitted_attr_name_expr[1:]
        # for i in input_data:
        #     values.append(i[lookup_key])
        values = [i[lookup_key] for i in input_data]

        input_data_new = values
        _get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)
    elif lookup_key == "*" and isinstance(input_data, dict):
        values = []
        lookup_key = splitted_attr_name_expr[1:2][0]
        splitted_attr_name_expr = splitted_attr_name_expr[1:]
        for key, value in input_data.items():
            if key == lookup_key:
                values.append(value)
            # print("values",values)

        input_data_new = values
        # print("1st data",splitted_attr_name_expr[1:])
        # print("2nd data",input_data_new)
        _get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)

    else:
        # return blank array
        return []


def provide(provider_inputs, input_data):
    # """Provides the value of the attribute from the input_data"""
    outputs = []
    input_resource_change_attrs = {}
    input_type = provider_inputs["operation_type"]
    resource_changes = input_data["resource_changes"]
    # CASE 1
    # - Get value of an attribute for all instances of a resource
    # - resource_changes.*.change.after.<attr_name>
    if input_type == "resource_changes":
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
                    evaluated_output = _get_expression_attribute(attribute, input_resource_change_attrs)
                    for val in evaluated_output:
                        outputs.append({"value": val, "meta": resource_change, "err": None})

        return outputs
    # CASE 2
    # - Get actions performed on a resource
    # - resource_changes.*.change.actions
    elif input_type == "resource_changes_actions":
        resource_type = provider_inputs["terraform_resource_type"]
        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                outputs.append(
                    {
                        "value": resource_change["change"]["actions"],
                        "meta": resource_change,
                        "err": None,
                    }
                )
        return outputs
    # CASE 3
    # - Get count of a particular resource
    # - resource_changes.*.index
    elif input_type == "resource_changes_count":
        count = 0
        resource_meta = {}
        resource_type = provider_inputs["terraform_resource_type"]
        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                resource_meta = resource_change
                count = max(count, resource_change["index"])

        outputs.append(
            {
                "value": count,
                "meta": resource_meta,
                "err": None,
            }
        )
        return outputs
    # CASE 4
    # TODO: Get relationship between resources
    return outputs
