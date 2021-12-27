package stackguardian.aws_s3_bucket.s3VersioningMfaFalse
#This package ensures that mfa_delete is false for the bucket

default isPassed = false

isPassed{
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_s3_bucket"
	input_resource_changes_attrs := input_resource_changes.change.after
    mfa := input_resource_changes_attrs.versioning[k]
    mfa.mfa_delete == false
#     traverse := sprintf("versioning[%d].mfa_delete", [i])
#     retVal := { "Id": bucket.id, "ReplaceType": "edit", "CodeType": "attribute", "Traverse": traverse, "Attribute": "versioning.mfa_delete", "AttributeDataType": "bool", "Expected": true, "Actual": mfa.mfa_delete }
}

# https://play.openpolicyagent.org/p/yBPeHJS9iT

