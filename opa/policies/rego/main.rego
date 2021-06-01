package stackguardian.terraform_plan

# based on data/data1_tf_plan_0_14_6_v2.json and tf_plan_0_14_6.json

_data := {
	"source_ref": "terraform_plan_json:0.14.6",
	"schema_version": "terraform_plan_json:0.0.1",
	"policies": {"terraform_plan": [
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
					"name": "acl",
					"type": "tf_provider_reserved",
					"evaluators": {
						"all_of": [{
							"evaluator_ref": "str_contains_str",
							"evaluator_data": "public-read",
						}],
						"any_of": [],
						"none_of": [],
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
						"any_of": [],
						"none_of": [],
					},
				},
			],
		},
	]},
}

overlapping_resource_attrs[msg] {
	# get list containg policies (maps) for terraform_plan key and begin iteration, triggered by [i] in the syntax where i is an arbitrary var
	policy_terraform_plan := _data.policies.terraform_plan[i]

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

	policy_attribute_evaluators_all_of := policy_attribute.evaluators.all_of

	evaluators := policy_attribute_evaluators_all_of[m]
	evaluator_ref := evaluators.evaluator_ref
	evaluator_data := evaluators.evaluator_data
	evaluator_datatype := type_name(evaluator_data)

	# TODO: Handle "null" datatype values

	evaluation_result := evaluator_handler(input_resource_changes_attr_value, evaluator_data, evaluator_ref)

	# 	policy_attribute_evaluators_any_of := policy_attribute.evaluators.any_of
	# 	policy_attribute_evaluators_none_of := policy_attribute.evaluators.none_of

	# As this is a partial polocy, we can return any data made accessible by above in any format, map in this case.
	msg := {"all_of": {policy_resource: {policy_attribute_name: [evaluator_ref, evaluator_data, input_resource_changes_attr_value, input_datatype, evaluator_datatype, evaluation_result]}}}
}

evaluator_handler(input_data, evaluator_data, evaluator_ref) = result {
	evaluator_ref == "str_equals_str"
	result := str_equals_str_new(input_data, evaluator_data)
} else = result {
	evaluator_ref == "str_contains_str"
	result := str_contains_str(input_data, evaluator_data)
} else = result {
	evaluator_ref == "str_in_list"
	result := str_in_list(input_data, evaluator_data)
} else = result {
	evaluator_ref == "equals_null"
	result := equals_null(input_data)
}

str_contains_str(input_data, evaluator_data) = "passed" {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "string"
	contains(input_data, evaluator_data)
} else = "For 'str_equals' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	not type_name(input_data) == "string"
} else = "For 'str_equals' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	not type_name(evaluator_data) == "string"
} else = "failed" {
	true
}

str_equals_str(input_data, evaluator_data) = "For 'str_equals' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	# TODO: Refactor redundancy
	type_check(input_data, "string", evaluator_data, "string")
} else = "passed" {
	input_data == evaluator_data
} else = "failed" {
	true
}

type_check(input_data, input_data_type, evaluator_data, evaluator_data_type) {
	not type_name(input_data) == input_data_type
}

type_check(input_data, input_data_type, evaluator_data, evaluator_data_type) {
	not type_name(evaluator_data) == evaluator_data_type
}

# functions str_equals + type_check put together
str_equals_str_new(input_data, evaluator_data) = "passed" {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "string"
	input_data == evaluator_data
} else = "For 'str_equals' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	not type_name(input_data) == "string"
} else = "For 'str_equals' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	not type_name(evaluator_data) == "string"
} else = "failed" {
	true
}

str_in_list(input_data, evaluator_data) = "passed" {
	type_name(input_data) == "string"
	type_name(evaluator_data) == "array"
	input_data == evaluator_data[_]
} else = "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'." {
	not type_name(input_data) == "string"
} else = "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'." {
	not type_name(evaluator_data) == "array"
} else = "failed" {
	true
}

equals_null(input_data) = "passed" {
	type_name(input_data) == "null"
} else = "failed" {
	true
}

# contains_str(input_data, evaluator_data) = result {
# type_name(evaluator_data) == "string"
# 	evaluator_data == input_data
# 	result := "passed"
# } else { result := "failed" }

# contained_in_cidr() {
# net.cidr_contains(cidr, cidr_or_ip)
# }
