package stackguardian.aws_s3_bucket.s3VersioningEnabled

default isPassed = false

isPassed = true{
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    mfa := input_resource_changes_attrs.versioning[k]
    mfa.enabled == true
}

# https://play.openpolicyagent.org/p/q1iJbftrlj