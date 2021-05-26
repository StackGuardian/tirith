package stackguardian

# based on data/data1_tf_plan_0_14_6_v2.json and tf_plan_0_14_6.json

result {
    some i
	input := input.resource_changes[i]
	data := data.policies
	str_in_list(input, data)
}

str_in_list(input, data) {
	input == data
}

str_in_str(input, data) {
	input == data
}
