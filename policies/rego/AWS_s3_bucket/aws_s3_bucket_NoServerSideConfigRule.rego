package stackguardian.aws_s3_bucket.Nos3ServerSideConfigRule

# Checks if there is no server side config

default isPassed = false

isPassed = true{
    input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    input_resource_changes_attrs.server_side_encryption_configuration == []
}

# https://play.openpolicyagent.org/p/6F2zuPhcIn



