package stackguardian.terraform_plan.deprecated


str_equals_str_v0(input_data, evaluator_data) = "For 'str_equals_str' evaluator_ref, both input_data and evaluator_data should be a 'string'." {
	# TODO: Refactor redundancy!
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
