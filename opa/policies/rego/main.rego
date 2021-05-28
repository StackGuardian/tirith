package stackguardian.terraform

# based on data/data1_tf_plan_0_14_6_v2.json and tf_plan_0_14_6.json

data := {
    "source_ref": "terraform_plan_json:0.14.6",
    "schema_version": "terraform_plan_json:0.0.1",
    "policies": {
        "terraform_plan": [
            {
                "resource_type": "aws_s3_bucket",
                "attributes": [
                    {
                        "name": "action",
                        "type": "tf_core_reserved",
                        "evaluators": {
                            "all_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "create"
                                    ]
                                }
                            ],
                            "any_of": [],
                            "none_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "destroy"
                                    ]
                                }
                            ],
                            "relations": []
                        }
                    },
                    {
                        "name": "count",
                        "type": "tf_core_reserved",
                        "evaluators": {
                            "all_of": [],
                            "any_of": [],
                            "none_of": []
                        }
                    },
                    {
                        "name": "acl",
                        "type": "tf_provider_reserved",
                        "evaluators": {
                            "all_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "public-read",
                                        "public"
                                    ]
                                }
                            ],
                            "any_of": [],
                            "none_of": []
                        }
                    }
                ]
            },
            {
                "resource_type": "null_resource",
                "attributes": [
                    {
                        "name": "action",
                        "type": "tf_core_reserved",
                        "evaluators": {
                            "all_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "create"
                                    ]
                                }
                            ],
                            "any_of": [],
                            "none_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "destroy"
                                    ]
                                }
                            ],
                            "relations": []
                        }
                    },
                    {
                        "name": "count",
                        "type": "tf_core_reserved",
                        "evaluators": {
                            "all_of": [],
                            "any_of": [],
                            "none_of": []
                        }
                    },
                    {
                        "name": "triggers",
                        "type": "tf_provider_reserved",
                        "evaluators": {
                            "all_of": [
                                {
                                    "evaluator_ref": "str_in_list",
                                    "evaluator_data": [
                                        "something"
                                    ]
                                }
                            ],
                            "any_of": [],
                            "none_of": []
                        }
                    }
                ]
            }
        ]
    }
}

overlapping_resource_attrs[msg] {
    policy_terraform_plan := data.policies.terraform_plan[i]
	policy_resource := policy_terraform_plan.resource_type
	policy_attributes := policy_terraform_plan.attributes

    policy_attribute := policy_attributes[j]
	policy_attribute_name := policy_attribute.name

	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == policy_resource
	input_resource_changes_attrs := input_resource_changes.change.after
    
    input_resource_changes_attrs[key]
	policy_attribute_name == key
	
	policy_attribute_evaluators_all_of := policy_attribute.evaluators.all_of
    
	evaluator_ref := policy_attribute_evaluators_all_of[m].evaluator_ref

# 	policy_attribute_evaluators_any_of := policy_attribute.evaluators.any_of
# 	policy_attribute_evaluators_none_of := policy_attribute.evaluators.none_of

	msg := {policy_resource: policy_attribute_name}
}
