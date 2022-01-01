package stackguardian.ec2.IMDSversion1Disabled

# Ensure Instance Metadata Service Version 1 is not enabled

default isPassed = false

isPassed  {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_instance"
	input_resource_changes_attrs := input_resource_changes.change.after_unknown
    metadata_options := input_resource_changes_attrs.metadata_options[0]
    http_token = metadata_options.http_token
    http_token = ["required"]
    http_endpoint = metadata_options.http_endpoint
    http_endpoint = ["disabled"]
}

# https://play.openpolicyagent.org/p/zdTLi0VbvI