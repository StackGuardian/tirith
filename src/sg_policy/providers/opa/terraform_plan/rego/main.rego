package stackguardian.terraform_plan.main

# import input._test_data as _data

initialize[msg] {
	# get list containg policies (list) from terraform_plan key and begin iteration, triggered by [i] in the syntax where i is an arbitrary var
	policy_terraform_plan := data.terraform_plan.policies[i]

	# During each assign the value of resource_type (str) from policy_terraform_plan map
	policy_resource := policy_terraform_plan.resource_type

	# During each assign the value of attributes (list) from policy_terraform_plan map
	policy_attributes := policy_terraform_plan.attributes

	policy_attribute := policy_attributes[j]
	policy_attribute_name := policy_attribute.name

	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == policy_resource
	input_resource_changes_attrs := input_resource_changes.change.after

	# get 'key' names from input_resource_changes_attrs map and begin iteration, triggered by [key] in the syntax where key is an arbitrary var
	input_resource_changes_attrs[key]

	# str comparision
	policy_attribute_name == key

	input_resource_changes_attr_value := input_resource_changes_attrs[key]
	input_datatype := type_name(input_resource_changes_attr_value)

	msg := {
		"policy_resource": policy_resource,
		"policy_attribute": policy_attribute,
		"policy_attribute_name": policy_attribute_name,
		"input_resource_changes_attr_value": input_resource_changes_attr_value,
		"input_datatype": input_datatype,
	}
}

all_of[msg] {
	# iterate over all_of map
	policy_attribute_evaluators_all_of := initialize[i].policy_attribute.evaluators.all_of
	evaluator_all_of := policy_attribute_evaluators_all_of[m]
	evaluator_ref_all_of := evaluator_all_of.evaluator_ref
	evaluator_data_all_of := evaluator_all_of.evaluator_data
	evaluator_datatype_all_of := type_name(evaluator_data_all_of)
	evaluation_result_all_of := evaluator_handler(initialize[i].input_resource_changes_attr_value, evaluator_data_all_of, evaluator_ref_all_of)

	# As this is a partial policy, we can return any data made accessible by above in any format, map in this case.
	msg := {
		"resource_type": initialize[i].policy_resource,
		"attribute": initialize[i].policy_attribute_name,
		"evaluator_ref": evaluator_ref_all_of,
		"evaluator_data": evaluator_data_all_of,
		"input_data": initialize[i].input_resource_changes_attr_value,
		# "input_datatype": initialize.input_datatype,
		# "evaluator_datatype": evaluator_datatype_all_of,
		"evaluation_result": evaluation_result_all_of,
	}
}

any_of[msg] {
	# iterate over any_of map
	policy_attribute_evaluators_any_of := initialize[i].policy_attribute.evaluators.any_of
	evaluator_any_of := policy_attribute_evaluators_any_of[m]
	evaluator_ref_any_of := evaluator_any_of.evaluator_ref
	evaluator_data_any_of := evaluator_any_of.evaluator_data
	evaluator_datatype_any_of := type_name(evaluator_data_any_of)
	evaluation_result_any_of := evaluator_handler(initialize[i].input_resource_changes_attr_value, evaluator_data_any_of, evaluator_ref_any_of)

	# As this is a partial policy, we can return any data made accessible by above in any format, map in this case.
	msg := {
		"resource_type": initialize[i].policy_resource,
		"attribute": initialize[i].policy_attribute_name,
		"evaluator_ref": evaluator_ref_any_of,
		"evaluator_data": evaluator_data_any_of,
		"input_data": initialize[i].input_resource_changes_attr_value,
		# "input_datatype": initialize.input_datatype,
		# "evaluator_datatype": evaluator_datatype_any_of,
		"evaluation_result": evaluation_result_any_of,
	}
}

none_of[msg] {
	# iterate over none_of map
	policy_attribute_evaluators_none_of := initialize[i].policy_attribute.evaluators.none_of
	evaluator_none_of := policy_attribute_evaluators_none_of[m]
	evaluator_ref_none_of := evaluator_none_of.evaluator_ref
	evaluator_data_none_of := evaluator_none_of.evaluator_data
	evaluator_datatype_none_of := type_name(evaluator_data_none_of)
	evaluation_result_none_of := evaluator_handler(initialize[i].input_resource_changes_attr_value, evaluator_data_none_of, evaluator_ref_none_of)

	# As this is a partial policy, we can return any data made accessible by above in any format, map in this case.
	msg := {
		"resource_type": initialize[i].policy_resource,
		"attribute": initialize[i].policy_attribute_name,
		"evaluator_ref": evaluator_ref_none_of,
		"evaluator_data": evaluator_data_none_of,
		"input_data": initialize[i].input_resource_changes_attr_value,
		# "input_datatype": initialize.input_datatype,
		# "evaluator_datatype": evaluator_datatype_none_of,
		"evaluation_result": evaluation_result_none_of,
	}
}

# general[msg] {
# 	# iterate over evaluator map
# 	policy_attribute_evaluators := initialize[i].policy_attribute.evaluators[EVALUATOR_TYPE]
# 	evaluator := policy_attribute_evaluators[m]
# 	evaluator_ref := evaluator.evaluator_ref
# 	evaluator_data := evaluator.evaluator_data
# 	evaluator_datatype := type_name(evaluator_data)
# 	evaluation_result := evaluator_handler(initialize[i].input_resource_changes_attr_value, evaluator_data, evaluator_ref)

# 	# As this is a partial policy, we can return any data made accessible by above in any format, map in this case.
# 	msg := {
# 		"resource_type": initialize[i].policy_resource,
# 		"attribute": initialize[i].policy_attribute_name,
# 		"evaluator_ref": evaluator_ref,
# 		"evaluator_data": evaluator_data,
# 		"input_data": initialize[i].input_resource_changes_attr_value,
# 		# "input_datatype": initialize.input_datatype,
# 		# "evaluator_datatype": evaluator_datatype,
# 		"evaluation_result": evaluation_result,
# 	}
# }

evaluators := {
	"all_of": all_of,
	"any_of": any_of,
	"none_of": none_of,
}

evaluator_handler(input_data, evaluator_data, evaluator_ref) = result {
	evaluator_ref == "str_equals_str"
	result := str_equals_str(input_data, evaluator_data)
} else = result {
	evaluator_ref == "str_contains_str"
	result := str_contains_str(input_data, evaluator_data)
} else = result {
	evaluator_ref == "str_in_list"
	result := str_in_list(input_data, evaluator_data)
} else = result {
	evaluator_ref == "equals_null"
	result := equals_null(input_data)
} else = result {
	evaluator_ref == "str_matches_regex"
	result := str_matches_regex(input_data, evaluator_data)
} else = result {
	evaluator_ref == "bool_equals_bool"
	result := bool_equals_bool(input_data, evaluator_data)
} else = result {
	evaluator_ref == "cidr_contains_cidr_or_ip"
	result := cidr_contains_cidr_or_ip(input_data, evaluator_data)
}

cidr_contains_cidr_or_ip(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "string"
	net.cidr_contains(evaluator_data, input_data)
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "string"
	msg := "For 'cidr_contains_cidr_or_ip' evaluator_ref, both input_data and evaluator_data should be cidr or ip as 'string'."
} else = {"pass": "undef", "message": msg} {
	not type_name(evaluator_data) == "string"
	msg := "For 'cidr_contains_cidr_or_ip' evaluator_ref, both input_data and evaluator_data should be cidr or ip as 'string'."
} else = {"pass": "undef", "message": msg} {
	not net.cidr_contains(evaluator_data, input_data)
	msg := sprintf("input data '%s' should be a valid cidr/ip and allowed data '%s' should be a valid cidr.", [input_data, evaluator_data])
} else = {"pass": false, "message": msg} {
	msg := sprintf("input cidr or ip '%s' is not contained in allowed cidr '%s'", [input_data, evaluator_data])
}

bool_equals_bool(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "boolean"
	type_name(evaluator_data) == "boolean"
	input_data == evaluator_data
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "boolean"
	msg := "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'."
} else = {"pass": "undef", "message": msg} {
	not type_name(evaluator_data) == "boolean"
	msg := "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'."
} else = {"pass": false, "message": msg} {
	msg := sprintf("input should be '%s'", [evaluator_data])
}

str_matches_regex(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "string"
	regex.is_valid(evaluator_data)
	regex.match(evaluator_data, input_data)
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not regex.is_valid(evaluator_data)
	msg := sprintf("Provided regex '%s' is not valid", [evaluator_data])
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "string"
	msg := "For 'str_matches_regex' evaluator_ref, input_data should be a 'string'."
} else = {"pass": false, "message": msg} {
	msg := sprintf("input string '%s' does not match regex '%s'", [input_data, evaluator_data])
}

str_contains_str(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "string"
	contains(evaluator_data, input_data)
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "string"
	msg := "For 'str_contains_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
} else = {"pass": "undef", "message": msg} {
	not type_name(evaluator_data) == "string"
	msg := "For 'str_contains_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
} else = {"pass": false, "message": msg} {
	msg := sprintf("input string '%s' is not contained in '%s'", [input_data, evaluator_data])
}

# functions str_equals + type_check put together
str_equals_str(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "string"
	input_data == evaluator_data
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "string"
	msg := "For 'str_equals_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
} else = {"pass": "undef", "message": msg} {
	not type_name(evaluator_data) == "string"
	msg := "For 'str_equals_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
} else = {"pass": false, "message": msg} {
	msg := sprintf("input string '%s' is not equal to '%s'", [input_data, evaluator_data])
}

str_in_list(input_data, evaluator_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "array"
	input_data == evaluator_data[_]
	msg := ""
} else = {"pass": "undef", "message": msg} {
	not type_name(input_data) == "string"
	msg := "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'."
} else = {"pass": "undef", "message": msg} {
	not type_name(evaluator_data) == "array"
	msg := "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'."
} else = {"pass": false, "message": msg} {
	msg := sprintf("input string '%s' is not present in allowed list '%s'", [input_data, evaluator_data])
}

equals_null(input_data) = {"pass": true, "message": msg} {
	type_name(input_data) == "null"
	msg := ""
} else = {"pass": false, "message": msg} {
	msg := sprintf("input data is of type '%s' which is not 'null'", [type_name(input_data)])
}

# TODO: Resource relationship exists
