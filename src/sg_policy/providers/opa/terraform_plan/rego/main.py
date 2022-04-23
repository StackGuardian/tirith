import input._test_data as _data
def initialize(data,input_data):
    policies=data["policies"]
    poli
	for policy in policies:
		policy_resource=policy["resource_type"]
		attributes=policy["attributes"]
		policy_attribute.append(attributes)
		for attribute in attributes:
			policy_attribute_name=attribute["name"]
	resource_changes=input_data["resource_changes"]
	for resource_change in resource_changes:
		if resource_change["type"]==policy_resource:
			input_resource_change_attrs=resource_change["changes"]["after"]
	for key,value in input_resource_change_attrs.items():
		input_resource_change_attr_value=value

def all_of(initialize):
	for i in range(len(initialize)):
	    policy_attribute_evaluators_all_of = initialize[i]["policy_attribute"]["evaluators"]["all_of"]
	    evaluator_all_of := policy_attribute_evaluators_all_of[m]
	    evaluator_ref_all_of := evaluator_all_of.evaluator_ref
	    evaluator_data_all_of := evaluator_all_of.evaluator_data
	    evaluator_datatype_all_of := type_name(evaluator_data_all_of)
	    evaluation_result_all_of := evaluator_handler(initialize[i].input_resource_changes_attr_value, evaluator_data_all_of, evaluator_ref_all_of)

