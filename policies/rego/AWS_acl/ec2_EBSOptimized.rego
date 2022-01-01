package stackguardian.aws_s3_bucket.ec2EBSOptimized

default isPassed = false

isPassed  {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_instance"
	input_resource_changes_attrs := input_resource_changes.change.after_unknown
    ebs_optimized := input_resource_changes_attrs.ebs_optimized
    ebs_optimized == true
}

# https://play.openpolicyagent.org/p/5G2Fkit7Zx