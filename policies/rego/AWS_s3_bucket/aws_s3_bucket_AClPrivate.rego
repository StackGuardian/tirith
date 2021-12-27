package stackguardian.aws_s3_bucket.ACLPrivate

default isPassed = false

isPassed = true{
    input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    acl = input_resource_changes_attrs.acl
    acl == "private"
}

# https://play.openpolicyagent.org/p/7vXGzmfbCJ