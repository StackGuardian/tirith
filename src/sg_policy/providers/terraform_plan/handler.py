import re
from time import time
import os
import json
from .utils import star_int_equals_int

# TODO: use CAMELCASE for all function name
# def func(splitted_attr_name_expr,input_data):

#   if len(splitted_attr_name_expr) == 0:

#     return input_data

#   lookup_key = splitted_attr_name_expr[0]

#   if lookup_key != "*":

#     if (type(input_data) == dict):
#       input_data_new = input_data[lookup_key]
#     elif type(input_data) == list:
#       input_data_new = input_data[0][lookup_key]
#     else:
#       input_data_new = input_data[lookup_key]
#     func(splitted_attr_name_expr[1:], input_data_new)

#   elif lookup_key == "*" and isinstance(input_data, list):

#     values = []

#     for i in input_data:

#         values.append(func(splitted_attr_name_expr[1:], i))

#     return values

#   else:

#     return "undef"


# input->(list [s3,acl,*],value of resource)
# returns->[any, any, any]
def get_expression_attribute(splitted_attr_name_expr, input_data):

    if len(splitted_attr_name_expr) == 0:

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

        get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)

    elif lookup_key == "*" and isinstance(input_data, list):
        print("lookup key    -", lookup_key)
        print("input_data    -", input_data)
        values = []
        lookup_key = splitted_attr_name_expr[1:2][0]
        splitted_attr_name_expr = splitted_attr_name_expr[1:]
        for i in input_data:
            # print(i)
            # print(lookup_key)

            values.append(i[lookup_key])
            # print("values",values)

        input_data_new = values
        # print("1st data",splitted_attr_name_expr[1:])
        # print("2nd data",input_data_new)
        get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)
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
        get_expression_attribute(splitted_attr_name_expr[1:], input_data_new)

    else:
        # return blank array
        return []


def find_item(obj, key):

    if key in obj:
        return obj[key]
    for v in obj.values():
        if isinstance(v, dict):
            item = find_item(v, key)
            if item is not None:
                return item
    return None


def find_input_resource_changes_value(chunks, input_resource_change_attrs):
    """Gives the filtered result after processing "*" and "." in query"""
    Iter_Count = 0
    if (
        len(chunks) > 1
        and len(input_resource_change_attrs[chunks[0]]) > 1
        and (type(input_resource_change_attrs[chunks[0]]) == dict)
    ):

        res = find_item(input_resource_change_attrs[chunks[0]], chunks[-1])

    elif (
        len(chunks) > 1
        and len(input_resource_change_attrs[chunks[0]]) == 1
        and type(input_resource_change_attrs[chunks[0]]) == list
    ):

        res = find_item(input_resource_change_attrs[chunks[0]][0], chunks[-1])

    elif (
        len(chunks) > 1
        and len(input_resource_change_attrs[chunks[0]]) > 1
        and type(input_resource_change_attrs[chunks[0]]) == list
    ):

        res = []

        for i in range(len(input_resource_change_attrs[chunks[0]])):
            each_res = find_item(input_resource_change_attrs[chunks[0]][i], chunks[-1])
            res.append(each_res)

    else:
        res = input_resource_change_attrs[chunks[0]]

    return res


# def find_item(chunks,input_resource_change_attrs):
# 	print(chunks[-1])
# 	print(input_resource_change_attrs[chunks[0]][0])
# 	s=finditem(input_resource_change_attrs[chunks[0]][0],chunks[-1])
# 	print(s)


def get_attribute_name(input_resource_change_attrs, chunks):

    if "*" in chunks:

        if type(input_resource_change_attrs[chunks[0]]) == list:

            res = find_input_resource_changes_value(chunks, input_resource_change_attrs)
            # print(res)
        else:

            res = "undef"
    elif len(chunks) > 1:
        if type(input_resource_change_attrs[chunks[0]]) == list:

            res = find_input_resource_changes_value(chunks, input_resource_change_attrs)
            res = res[0]
        else:

            res = "undef"

    else:
        res = find_input_resource_changes_value(chunks, input_resource_change_attrs)
        if len(chunks) > 1:
            res = res[0]

    try:
        input_changes = int(res)

    except:
        input_changes = res
    return input_changes


def provide(provider_inputs, input_data):
    # """Provides the value of the attribute from the input_data"""
    outputs = []
    input_resource_change_attrs = {}
    input_type = provider_inputs["input_type"]
    resource_changes = input_data["resource_changes"]
    # CASE 1
    # - Get value of an attribute for all instances of a resource
    # - resource_changes.*.change.after.<attr_name>
    if input_type == "resource_changes":
        attribute = provider_inputs["attribute"]
        resource_type = provider_inputs["resource_type"]

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
                    evaluated_output = get_expression_attribute(
                        attribute, input_resource_change_attrs
                    )
                    for val in evaluated_output:
                        outputs.append(
                            {"value": val, "meta": resource_change, "err": None}
                        )

        return outputs
    # CASE 2
    # - Get actions performed on a resource
    # - resource_changes.*.change.actions
    elif input_type == "resource_changes_actions":
        resource_type = provider_inputs["resource_type"]
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
        resource_type = provider_inputs["resource_type"]
        for resource_change in resource_changes:
            if resource_change["type"] == resource_type:
                resource_meta = resource_change
                count = min(count, resource_change["index"])

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


def provide_old(policy, input_data):
    """this function arranges the input changes per resource included in policy"""
    policies = policy["terraform_plan"]["policies"]
    policy_resource = []
    policy_attribute_name = []
    policy_attribute = []
    input_resource_changes_attr_value = []
    input_datatype = []
    policy_attribute_name = []
    input_resource_change_attrs = {}
    new_policy_attribute = []
    new_policy_attribute_name = []
    count = 0
    iter_count = 0
    Iter_count = []
    if len(policies) > 0:
        for policy in policies:
            policy_resource.append(policy["resource_type"])
            attributes = policy["attributes"]
        resource_changes = input_data["resource_changes"]
        for resource_change in resource_changes:
            if resource_change["type"] in policy_resource:
                input_resource_change_attrs = resource_change["change"]["after"]
        # print(input_resource_change_attrs)
        for attribute in attributes:
            count = 1
            chunks = attribute["name"].split(".")
            s = chunks[0]
            if chunks[0] in input_resource_change_attrs:
                count += 1
                policy_attribute.append(attribute)
                policy_attribute_name.append(attribute["name"])
                input_changes = get_attribute_name(input_resource_change_attrs, chunks)

                msg_new = get_expression_attribute(chunks, input_resource_change_attrs)
                print(msg_new)
    # print(iter_count)

    msg = {
        "policy_resource": policy_resource,
        "policy_attribute": policy_attribute,
        "policy_attribute_name": policy_attribute_name,
        "input_resource_changes_attr_value": input_resource_changes_attr_value,
        "input_datatype": input_datatype,
        "iter_count": Iter_count,
    }
    # print(input_resource_changes_attr_value)
    return msg
