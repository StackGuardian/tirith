# Ensure all data stored in the S3 bucket is securely encrypted at rest

package stackguardian.aws_s3_bucket.s3Encryption

default isPassed = false

isPassed = true{
    input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    server_side_encryp_config := input_resource_changes_attrs.server_side_encryption_configuration[k]
    sse_algorithm = server_side_encryp_config.rule.apply_server_side_encryption_by_default.sse_algorithm
    sse_algorithm == "AES256"
}

isPassed = true{
    input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    server_side_encryp_config := input_resource_changes_attrs.server_side_encryption_configuration[k]
    sse_algorithm = server_side_encryp_config.rule.apply_server_side_encryption_by_default.sse_algorithm
    sse_algorithm == "aws:kms"
}

# https://play.openpolicyagent.org/p/oDRb1DST2h