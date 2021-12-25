package stackguardian.aws_s3_bucket.NoWebsiteIndexDocument

default isPassed = true

isPassed = false {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    website := input_resource_changes_attrs.website[k]
    website_attr := website.index_document
}

# https://play.openpolicyagent.org/p/Bcd3s6FrFW