package stackguardian.aws_s3_bucket.EC2PublicIP

# EC2 instance should not have public IP.

default isPassed = true

isPassed = false  {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_instance"
	input_resource_changes_attrs := input_resource_changes.change.after_unknown
    associate_public_ip_address := input_resource_changes_attrs.associate_public_ip_address
    associate_public_ip_address = true
}

#https://play.openpolicyagent.org/p/gIrjqhglyc