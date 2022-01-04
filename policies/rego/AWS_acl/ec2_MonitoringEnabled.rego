package stackguardian.ec2.MontitoringEnabled

# Ensure that detailed monitoring is enabled for EC2 instances

default isPassed = false

isPassed  {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_instance"
	input_resource_changes_attrs := input_resource_changes.change.after
    monitoring := input_resource_changes_attrs.monitoring
    monitoring == true
}

# https://play.openpolicyagent.org/p/ukzTlohhLh