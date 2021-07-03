package stackguardian.terraform_plan.main

_data := {"terraform_plan": {
	"source_terraform_version": "0.14.6",
	"generated_from": "terraform_plan",
	"applicable_on": "terraform_plan",
	"schema_version": "0.0.1",
	"policies": [
		{
			"resource_type": "aws_s3_bucket",
			"attributes": [
				{
					"name": "action",
					"type": "tf_core_reserved",
					"evaluators": {
						"all_of": [{
							"evaluator_ref": "str_in_list",
							"evaluator_data": ["create"],
						}],
						"any_of": [],
						"none_of": [{
							"evaluator_ref": "str_in_list",
							"evaluator_data": ["destroy"],
						}],
					},
				},
				{
					"name": "count",
					"type": "tf_core_reserved",
					"evaluators": {
						"all_of": [],
						"any_of": [],
						"none_of": [],
					},
				},
				{
					"name": "acl",
					"type": "tf_provider_reserved",
					"evaluators": {
						"all_of": [
							{
								"evaluator_ref": "str_matches_regex",
								"evaluator_data": "public-r323j**D",
							},
							{
								"evaluator_ref": "str_contains_str",
								"evaluator_data": "public",
							},
						],
						"any_of": [{
							"evaluator_ref": "cidr_contains_cidr_or_ip",
							"evaluator_data": "public-r323j**D",
						}],
						"none_of": [{
							"evaluator_ref": "str_matches_regex",
							"evaluator_data": "public-r323j**D",
						}],
					},
				},
				{
					"name": "force_destroy",
					"type": "tf_provider_reserved",
					"evaluators": {
						"all_of": [{
							"evaluator_ref": "bool_equals_bool",
							"evaluator_data": true,
						}],
						"any_of": [{
							"evaluator_ref": "bool_equals_bool",
							"evaluator_data": "true",
						}],
						"none_of": [{
							"evaluator_ref": "bool_equals_bool",
							"evaluator_data": false,
						}],
					},
				},
			],
		},
		{
			"resource_type": "null_resource",
			"attributes": [
				{
					"name": "action",
					"type": "tf_core_reserved",
					"evaluators": {
						"all_of": [{
							"evaluator_ref": "str_in_list",
							"evaluator_data": ["create"],
						}],
						"any_of": [],
						"none_of": [{
							"evaluator_ref": "str_in_list",
							"evaluator_data": ["destroy"],
						}],
						"relations": [],
					},
				},
				{
					"name": "count",
					"type": "tf_core_reserved",
					"evaluators": {
						"all_of": [],
						"any_of": [],
						"none_of": [],
					},
				},
				{
					"name": "triggers",
					"type": "tf_provider_reserved",
					"evaluators": {
						"all_of": [{
							"evaluator_ref": "equals_null",
							"evaluator_data": "something",
						}],
						"any_of": [{
							"evaluator_ref": "equals_null",
							"evaluator_data": "something",
						}],
						"none_of": [{
							"evaluator_ref": "equals_null",
							"evaluator_data": "something",
						}],
					},
				},
			],
		},
	],
}}

policy_result[msg] {
	# evaluations := {}

	# get list containg policies (list) from terraform_plan key and begin iteration, triggered by [i] in the syntax where i is an arbitrary var
	policy_terraform_plan := _data.terraform_plan.policies[i]

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

	# iterate over all_of map
	policy_attribute_evaluators_all_of := policy_attribute.evaluators.all_of
	evaluator_all_of := policy_attribute_evaluators_all_of[m]
	evaluator_ref_all_of := evaluator_all_of.evaluator_ref
	evaluator_data_all_of := evaluator_all_of.evaluator_data
	evaluator_datatype_all_of := type_name(evaluator_data_all_of)
	evaluation_result_all_of := evaluator_handler(input_resource_changes_attr_value, evaluator_data_all_of, evaluator_ref_all_of)

	# iterate over any_of map
	policy_attribute_evaluators_any_of := policy_attribute.evaluators.any_of
	evaluator_any_of := policy_attribute_evaluators_any_of[n]
	evaluator_ref_any_of := evaluator_any_of.evaluator_ref
	evaluator_data_any_of := evaluator_any_of.evaluator_data
	evaluator_datatype_any_of := type_name(evaluator_data_any_of)
	evaluation_result_any_of := evaluator_handler(input_resource_changes_attr_value, evaluator_data_any_of, evaluator_ref_any_of)

	# iterate over none_of map
	policy_attribute_evaluators_none_of := policy_attribute.evaluators.none_of
	evaluator_none_of := policy_attribute_evaluators_none_of[o]
	evaluator_ref_none_of := evaluator_none_of.evaluator_ref
	evaluator_data_none_of := evaluator_none_of.evaluator_data
	evaluator_datatype_none_of := type_name(evaluator_data_none_of)
	evaluation_result_none_of := evaluator_handler(input_resource_changes_attr_value, evaluator_data_none_of, evaluator_ref_none_of)

	# As this is a partial polocy, we can return any data made accessible by above in any format, map in this case.
	msg := {
		"resource_type": policy_resource,
		"attributes": [{
			"name": policy_attribute_name,
			"evalutors": {
				"all_of": [{
					"evaluator_ref": evaluator_ref_all_of,
					"evaluator_data": evaluator_data_all_of,
					"input_data": input_resource_changes_attr_value,
					# "input_datatype": input_datatype,
					# "evaluator_datatype": evaluator_datatype_all_of,
					"result": evaluation_result_all_of,
				}],
				"any_of": [{
					"evaluator_ref": evaluator_ref_any_of,
					"evaluator_data": evaluator_data_any_of,
					"input_data": input_resource_changes_attr_value,
					# "input_datatype": input_datatype,
					# "evaluator_datatype": evaluator_datatype_any_of,
					"result": evaluation_result_any_of,
				}],
				"none_of": [{
					"evaluator_ref": evaluator_ref_none_of,
					"evaluator_data": evaluator_data_none_of,
					"input_data": input_resource_changes_attr_value,
					# "input_datatype": input_datatype,
					# "evaluator_datatype": evaluator_datatype_none_of,
					"result": evaluation_result_none_of,
				}],
			},
		}],
	}
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
	msg := sprintf("input string '%s' is not equal to '%s'", [input_data, evaluator_data])
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
