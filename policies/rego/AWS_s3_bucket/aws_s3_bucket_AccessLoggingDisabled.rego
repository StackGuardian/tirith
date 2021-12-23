package stackguardian.aws_s3_bucket.AccessLoggingDisabled

default isPassed = false

isPassed = true{
    input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    logging := input_resource_changes_attrs.logging
  	logging != null
  	logging != []
    logging != "undefined"
}

# When you join multiple expressions together in a query you are expressing logical AND.

# To express logical OR in Rego you define multiple rules with the same name.

# https://play.openpolicyagent.org/p/jbLzwBClf1
